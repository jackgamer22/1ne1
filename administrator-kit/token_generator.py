import hashlib

def generate_token(hwid):
    """
    Generates an activation token for a given HWID.
    This must use the same secret salt as the main sms_sender.py script.
    """
    secret_salt = "magxxxicvot_secret"
    token = hashlib.sha256((hwid + secret_salt).encode()).hexdigest()
    return token

if __name__ == '__main__':
    print("***************************************************")
    print("*                                                 *")
    print("*       MagxxxicVot Admin Token Generator         *")
    print("*                                                 *")
    print("***************************************************\n")

    hwid = input("Enter User HWID: ").strip()
    if hwid:
        token = generate_token(hwid)
        print(f"\n[SUCCESS] Generated Token: {token}")
        print("\nSend this token to the user to activate their software.")
    else:
        print("\n[ERROR] HWID cannot be empty.")
