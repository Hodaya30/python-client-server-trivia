import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****
import sys

MAX_MSG_LENGTH = 10024
ERROR_MSG = "Error! "
SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
ERROR_RETURN = None
DATA_DELIMITER = "#"


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    full_msg = chatlib.build_message(code, data)
    conn.send(full_msg.encode())
    print("[CLIENT] ", full_msg)  # Debug print


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    full_msg = conn.recv(MAX_MSG_LENGTH).decode()
    cmd, data = chatlib.parse_message(full_msg)
    print("[CLIENT] ", full_msg)  # Debug print
    print(cmd, data)
    return cmd, data


def build_send_recv_parse(conn, code, data):
    build_and_send_message(conn, code, data)
    msg_code, data = recv_message_and_parse(conn)
    return msg_code, data


def get_score(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["my_score"], "")
    if cmd != chatlib.PROTOCOL_SERVER["your_score"]:
        error_and_exit(data)
    else:
        print("Your score is:", data, "points.")


def get_high_score(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["high_score"], "")
    if cmd != chatlib.PROTOCOL_SERVER["all_score"]:
        error_and_exit(data)
    else:
        print("\nThe score of all players:\n" + data)


def connect():
    """
        Creates new listening socket and returns it
        Recieves: -
        Returns: the socket object
        """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket


def error_and_exit(error_msg):
    """
       Send error message with given message
       Recieves: socket, message error string from called function
       Returns: None
       """
    print("XXX Error found: XXX\n", error_msg)
    sys.exit()


def login(conn):
    username = input("Please enter username: \n")
    password = input("Please enter your password: \n")
    login_msg = username + chatlib.DATA_DELIMITER + password
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], login_msg)
    answer = recv_message_and_parse(conn)
    while answer[0] != chatlib.PROTOCOL_SERVER["login_ok_msg"]:
        print("\nERROR! " + answer[1])
        username = input("Please enter username: \n")
        password = input("Please enter your password: \n")
        login_msg = username + chatlib.DATA_DELIMITER + password
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], login_msg)
        answer = recv_message_and_parse(conn)
    print("logged-in")


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")
    print("goodbye")

def play_question(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question"], "")
    if cmd == chatlib.PROTOCOL_SERVER["no_question"]:
        print("There is no available questions for you.")
        return ERROR_RETURN
    if cmd == chatlib.PROTOCOL_SERVER["error_msg"]:
        error_and_exit(cmd)
    elif cmd == chatlib.PROTOCOL_SERVER["your_question"]:
        quest_data = data.split(chatlib.DATA_DELIMITER)
        id = quest_data[0]
        question = quest_data[1]
        answers = [quest_data[2], quest_data[3], quest_data[4], quest_data[5]]
        print("\n Q: ", question)
        for i in range(4):
            print("\t"+str(i+1)+":\t"+answers[i])
        try_ans = input("Enter the number of your choice: ")
        score = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer"], id+chatlib.DATA_DELIMITER+try_ans)
        if score[0] == chatlib.PROTOCOL_SERVER["correct_answer"]:
            print("Correct!")
        elif score[0] == chatlib.PROTOCOL_SERVER["wrong_answer"]:
            print("Wrong... the correct answer is: #"+score[1])
        elif score[0]== chatlib.PROTOCOL_SERVER["No_cheating"]:
            print("Without cheating, you did not answer the question asked")
        else:
            error_and_exit(score[1])


def get_logged_users(conn):
    logged_users = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged"], "" )
    if logged_users[0] == chatlib.PROTOCOL_SERVER["logged_answer"]:
        print("Logged_users:\n" + logged_users[1])
    else:
        error_and_exit(logged_users[1])




def main():
    # Implement code
    my_socket = connect()
    login(my_socket)
    choice = input("""
            p       Play a trivia question
            s       Get my score
            h       Get highscore
            l       Get logged users
            q       Quit
            -Enter your choice: """)
    while choice != "q":
        if choice == "p":
            play_question(my_socket)
        elif choice == "s":
            get_score(my_socket)
        elif choice == "h":
            get_high_score(my_socket)
        elif choice == "l":
            get_logged_users(my_socket)
        else:
            print("Enter the letter of your choice: ")

        choice = input("""
        p       Play a trivia question
        s       Get my score
        h       Get highscore
        l       Get logged users
        q       Quit
        -Enter your choice: """)
    print("Bye!")
    logout(my_socket)
    my_socket.close()


if __name__ == '__main__':
    main()