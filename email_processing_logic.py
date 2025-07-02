import csv
import smtplib
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from pathlib import Path

# --------------------------------------------
# SMTP Deliverability Check
# --------------------------------------------
def smtp_check(email):
    domain = email.split('@')[-1]
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(mx_records[0].exchange)
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_record)
        server.helo("localhost")
        server.mail("you@example.com")
        code, _ = server.rcpt(email)
        server.quit()
        return code in [250, 251]
    except:
        return False

# --------------------------------------------
# Validate Email (Format + MX + SMTP)
# --------------------------------------------
def validate_single_email(email):
    try:
        email = email.strip()
        validate_email(email, check_deliverability=False)  # Format check
    except EmailNotValidError:
        return (email, 'invalid_format')

    domain = email.split('@')[1]
    try:
        if not dns.resolver.resolve(domain, 'MX'):
            return (email, 'dead')
    except:
        return (email, 'dead')

    return (email, 'live' if smtp_check(email) else 'dead')

# --------------------------------------------
# Process Emails in Threaded Batch
# --------------------------------------------
def process_emails(input_path, output_dir='output', status_updater=None, task_id=None):
    seen = set()
    results = []
    stats = defaultdict(int)

    # Ensure output directory for this specific task exists
    task_output_dir = Path(output_dir) / str(task_id) if task_id else Path(output_dir)
    task_output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as f:
        raw_emails = [line.strip() for line in f if line.strip()]

    stats['total_loaded'] = len(raw_emails)

    unique_emails = []
    for email in raw_emails:
        if email not in seen:
            seen.add(email)
            unique_emails.append(email)
        else:
            stats['duplicates_removed'] += 1

    stats['total_to_validate'] = len(unique_emails)
    emails_processed = 0

    if status_updater and task_id:
        status_updater(task_id, emails_processed, stats['total_to_validate'], dict(stats))

    with ThreadPoolExecutor(max_workers=50) as executor:
        # Using submit to get futures if we want to update progress more granularly
        # For now, executor.map is fine, and we'll update progress based on iteration

        futures = {executor.submit(validate_single_email, email): email for email in unique_emails}
        for future in ThreadPoolExecutor()._threads: # Workaround to iterate as completed with map-like behavior
            try:
                email, status = future.result()
                results.append((email, status))
                stats[status] += 1
                emails_processed += 1
                if status_updater and task_id and emails_processed % 50 == 0: # Update every 50 emails
                    status_updater(task_id, emails_processed, stats['total_to_validate'], dict(stats))
            except Exception as e:
                # Handle potential errors from validate_single_email if necessary
                print(f"Error processing email: {e}")
                stats['errors'] += 1
                emails_processed += 1 # Still count as processed

    if status_updater and task_id: # Final update
        status_updater(task_id, emails_processed, stats['total_to_validate'], dict(stats))

    # Write results
    with open(task_output_dir / "valid_emails.txt", "w", encoding='utf-8') as txt_file:
        for email, status in results:
            if status == "live":
                txt_file.write(email + "\n")

    with open(task_output_dir / "results.csv", "w", newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Email", "Status"])
        writer.writerows(results)

    print("--- Summary ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    return stats

# --------------------------------------------
# Run
# --------------------------------------------
if __name__ == "__main__":
    input_file = "UTF-8result_1.txt"  # example
    stats = process_emails(input_file)
