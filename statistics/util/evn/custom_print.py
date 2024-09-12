def print_status_message(message, message_type=None):
    if message_type == 'info':
        print('\033[90m' +'[*] '+ message + '\033[0m') # 90m is for grey color
    elif message_type == 'error':
        print('\033[91m' +'[-] '+ message + '\033[0m') # 91m is for red color
    elif message_type == 'success':
        print('\033[92m' +'[+] '+ message + '\033[0m') # 92m is for green color
    else:
        print(message) # if the type is not specified, just print the message as is