# UCL input validation module

# validate the provided username
def user(username):
    # usernames must exist and be 7 characters
    if (len(username) != 7):
        raise ValueError("Invalid username, must be 7 characters: {}".format(username))
# end user

# Validate the provided SSH key. sshpubkeys 2.2.0 currently supports
# ssh-rsa, ssh-dss (DSA), ssh-ed25519 and ecdsa keys with NIST curves.
def ssh_key(key_string):
    import sshpubkeys
    from sshpubkeys import SSHKey

    key = SSHKey(key_string, strict_mode=True)
    try:
        key.parse()
    except sshpubkeys.exceptions.InvalidTypeException as err:
        print("Invalid/unrecognised key type:", err)
        exit(1)
    except sshpubkeys.exceptions.TooShortKeyException as err:
        print("Key too short:", err)
        exit(1)
    except sshpubkeys.exceptions.InvalidKeyLengthException as err:
        print("Key length too short or too long:", err)
        exit(1)
    except sshpubkeys.exceptions.TooLongKeyException as err:
        print("Key too long:", err)
        exit(1)
    except sshpubkeys.exceptions.MalformedDataException as err:
        print("Malformed data - key may be corrupted, truncated or include extra content:", err)
        exit(1)
    except sshpubkeys.exceptions.InvalidKeyException as err:
        print("Invalid key:", err)
        exit(1)
    except NotImplementedError as err:
        print("Invalid/unsupported key type:", err)
        exit(1)
# end ssh_key

# Check that this is a UCL user and a username was provided
def ucl_user(email, username):
    if ("ucl.ac.uk" in email and username == None):
        print ("This is a UCL email address - please provide the user's UCL username with -u USERNAME")
        exit(1)
    if ("ucl.ac.uk" in email and username.startswith("mmm") ):
        print ("This is a UCL email address and you have specified an mmm username")
        exit(1)

# Check that this MMM username is in the range we have created
def mmm_username_in_range(username):
    # the highest mmm account currently existing
    MAX_ACCOUNT_NO = 600
    if username.startswith("mmm"):
        number = int(username[len(prefix):])
        if number > MAX_ACCOUNT_NO:
            print("Username "+username+ "does not exist. The last existing MMM account is " + MAX_ACCOUNT_NO)
            exit(1)
        elif number > MAX_ACCOUNT_NO-100:
            print("WARNING: last existing MMM role account is " + MAX_ACCOUNT_NO + ", we need to request more from ISD.User Services.")

