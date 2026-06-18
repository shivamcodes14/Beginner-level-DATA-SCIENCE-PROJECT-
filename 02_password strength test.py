while True:
    print("\n==================================")
    print("Password Strength Checker")
    print("==================================")

    password = input("Enter your password: ")
    length = len(password)

    has_uppercase = False
    has_lowercase = False
    has_digit = False
    has_special = False

    for char in password:
        if char.isupper():
            has_uppercase = True
        if char.islower():
            has_lowercase = True
        if char.isdigit():
            has_digit = True
        if not char.isalnum():
            has_special = True

    print("\n--- Password Analysis ---")
    print(f"Length: {length} characters")

    # Updated minimum length to 8 for better modern security
    if length < 8:
        print("\nResult: WEAK PASSWORD")
        print("Reason: Your password is too short (minimum 8 characters are required)")
    elif has_uppercase and has_lowercase and has_digit and has_special:
        print("\nResult: STRONG PASSWORD")
        print("Reason: Your password has uppercase, lowercase, digits, and special characters")
    else:
        print("\nResult: ACCEPTABLE PASSWORD")
        print("Suggestions to improve your password:")

        if not has_uppercase:
            print("- Add at least one uppercase letter")
        if not has_lowercase:
            print("- Add at least one lowercase letter")
        if not has_digit:
            print("- Add at least one digit")
        if not has_special:
            print("- Add at least one special character (@, #, $, etc.)")

    # Added .strip() to handle accidental spaces
    retry = input("\nDo you want to test another password? (yes/no): ").lower().strip()
    if retry != "yes":
        print("\nThank you for using Password Strength Checker.")
        break