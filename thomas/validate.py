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
    from sshpubkeys import SSHKey

    key = SSHKey(key_string, strict_mode=True)
    try:
        key.parse()
    except InvalidKeyException as err:
        print("Invalid key:", err)
        exit(1)
    except NotImplementedError as err:
        print("Invalid/unsupported key type:", err)
        exit(1)
# end ssh_key

