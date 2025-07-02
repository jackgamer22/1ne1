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
        # Ensure that dns.resolver.resolve returns a non-empty list for MX records
        mx_resolution = dns.resolver.resolve(domain, 'MX')
        if not mx_resolution: # Check if the list is empty
            return (email, 'dead')
    except: # Catches NXDOMAIN, NoAnswer, Timeout, etc.
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

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_emails = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        if status_updater and task_id:
            stats['error_message'] = f"Input file not found: {input_path}"
            status_updater(task_id, 0, 0, dict(stats), "error")
        print(f"Error: Input file not found at {input_path}")
        return stats # Or raise an error

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
        status_updater(task_id, emails_processed, stats['total_to_validate'], dict(stats), "processing")

    with ThreadPoolExecutor(max_workers=50) as executor:
        # Using a list of futures to properly track completion and handle results
        future_to_email = {executor.submit(validate_single_email, email): email for email in unique_emails}
        for future in concurrent.futures.as_completed(future_to_email):
            email_original = future_to_email[future]
            try:
                email, status = future.result()
                results.append((email, status))
                stats[status] += 1
            except Exception as e:
                print(f"Error processing email {email_original}: {e}")
                stats['errors'] += 1
                results.append((email_original, 'error_processing')) # Log processing error for this email
            finally:
                emails_processed += 1
                if status_updater and task_id and (emails_processed % 50 == 0 or emails_processed == stats['total_to_validate']):
                    current_status_str = "completed" if emails_processed == stats['total_to_validate'] else "processing"
                    status_updater(task_id, emails_processed, stats['total_to_validate'], dict(stats), current_status_str)

    # Write results
    valid_emails_file = task_output_dir / "valid_emails.txt"
    results_csv_file = task_output_dir / "results.csv"

    with open(valid_emails_file, "w", encoding='utf-8') as txt_file:
        for email, status in results:
            if status == "live":
                txt_file.write(email + "\n")

    with open(results_csv_file, "w", newline='', encoding='utf-8') as csv_file:
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
    # Example usage:
    # Create a dummy email_list.txt for testing
    # with open("email_list.txt", "w") as f:
    #     f.write("test@example.com\n")
    #     f.write("invalid-email\n")
    #     f.write("another@nonexistentdomain123abc.com\n")
    #     f.write("valid@gmail.com\n")

    input_file = "email_list.txt"  # Make sure this file exists in the same directory when running directly

    # Dummy status updater for direct script execution
    def print_status(task_id, processed, total, current_stats_dict, overall_status):
        print(f"Task {task_id} Status: {overall_status} - Processed {processed}/{total} - Stats: {current_stats_dict}")

    stats = process_emails(input_file, output_dir='output_direct_run', status_updater=print_status, task_id='direct_run_test')
    print("\nFinal Stats from direct run:", stats)
