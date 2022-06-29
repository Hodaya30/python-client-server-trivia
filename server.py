##############################################################################
# server.py
##############################################################################

import socket
import chatlib
import select
import random
import json
import requests

# GLOBALS
client_question=0
users = {}
questions = {}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
messages_to_send = []

MAX_MSG_LENGTH = 10024
ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"

# HELPER SOCKET METHODS

def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    full_msg = chatlib.build_message(code, data)
    messages_to_send.append((conn, full_msg.encode()))
    print("[SERVER] ", conn.getpeername(), full_msg)  # Debug print


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
    return cmd, data


# Data Loaders #
def load_questions_from_web():
    """
        Loads questions bank from file
        Recieves: -
        Returns: questions dictionary
        """
    global questions
    web_q = requests.get("https://opentdb.com/api.php?amount=50&type=multiple")
    json_content = json.loads(web_q.content)
    del json_content["response_code"]
    questions_json = json_content["results"]
    for index_question, question in enumerate(questions_json):
        correct_answer = question["correct_answer"]
        all_answers = [correct_answer]+question["incorrect_answers"]
        random.shuffle(all_answers)
        correct_answer_index = all_answers.index(correct_answer)+1
        # important! - converting from 'XML\CSS\HTML' format to 'utf-8'
        fixed_replaced_question = question["question"].replace("&#039;", "'").replace("&quot;", "'")
        # discarding specific question if it still has unwelcomed characters
        if (fixed_replaced_question.find('#') != -1 or fixed_replaced_question.find('|') != -1):
            break
        questions[str(index_question)] = {
            "question": fixed_replaced_question,
            "answers": all_answers,
            "correct": correct_answer_index
        }
    return questions

def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    global questions
    # questions = {
    #     2313: {"question": "How much is 2+2", "answers": ["3", "4", "2", "1"], "correct": 2},
    #     4122: {"question": "What is the capital of France?", "answers": ["Lion", "Marseille", "Paris", "Montpellier"],
    #            "correct": 3}
    # }
    questions_file = open("questions.txt", "r")
    content = questions_file.read()
    q = json.loads(content)
    questions = {int(k): (v) for k, v in q.items()}

    return questions


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    global users
    users_file = open("users.txt", "r")
    content = users_file.read()
    # users = {
    #     "test": {"password": "test", "score": 0, "questions_asked": []},
    #     "yossi": {"password": "123", "score": 50, "questions_asked": []},
    #     "master": {"password": "master", "score": 200, "questions_asked": []}
    # }
    users = json.loads(content)
    return users


# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    Receives: -
    Returns: the socket object
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.listen()
    print("listening....")

    return sock


def handle_logged_message(conn):
    logged = ",".join(logged_users.values())
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["logged_answer"], logged)


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], error_msg)


##### MESSAGE HANDLING


def handle_getscore_message(conn, username):
    global users
    score = users[username]["score"]
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_score"], str(score))


def handle_highscore_message(conn):
    global users
    high_score = sorted(users, key=lambda u: users[u]["score"], reverse=True)
    # build high_score data in string
    high_score_data = ""
    for user in high_score:
        high_score_data = high_score_data + "\t" + user + ":" + str(users[user]["score"]) + "\n"
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["all_score"], high_score_data)


def handle_logout_message(conn):
    """
    Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: None
    """
    global logged_users
    user = conn.getpeername()
    if user in logged_users:
        print("the user: {" + logged_users.pop(user) + "} logout and disconnected")
    else:
        print("the user disconnected")
    conn.close()


def is_login(conn):
    return conn.getpeername() in logged_users


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users  # To be used later
    [username, password] = chatlib.split_data(data, 2)
    if username in users:
        if users[username]["password"] == password:
            if not is_login(conn):
                build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
                logged_users[conn.getpeername()] = username
            else:
                send_error(conn, "this user already login")
        else:
            send_error(conn, "the password didn't match")
    else:
        send_error(conn, "the username doesn't exist")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users  # To be used later
    if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
        handle_login_message(conn, data)
    elif cmd == chatlib.PROTOCOL_CLIENT["my_score"]:
        handle_getscore_message(conn, logged_users[conn.getpeername()])
    elif cmd == chatlib.PROTOCOL_CLIENT["high_score"]:
        handle_highscore_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
        handle_logout_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["logged"]:
        handle_logged_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_question"]:
        handle_question_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["send_answer"]:
        handle_answer_message(conn, logged_users[conn.getpeername()], data)
    elif not is_login(conn):
        send_error(conn, "command before login")

    else:
        send_error(conn, "command didn't recognized")


def print_client_socket(client_sockets):
    for c in client_sockets:
        address = c.getpeername()
        print("IP: ", address[0], "PORT: ", str(address[1]))


def create_random_question(username):

    if len(questions) == len(users[username]["questions_asked"]):
        return None
    else:
        question_num = random.choice(list(questions.keys()))
        question = questions[question_num]
        while question_num in users[username]["questions_asked"]:
            question_num = random.choice(list(questions.keys()))
            question = questions[question_num]
    your_question = str(question_num) + chatlib.DATA_DELIMITER + question["question"] + chatlib.DATA_DELIMITER + \
    chatlib.DATA_DELIMITER.join(question["answers"]) + chatlib.DATA_DELIMITER + str(question["correct"])
    users[username]["questions_asked"].append(question_num)
    return your_question


def handle_question_message(conn):
    global client_question
    q = create_random_question(logged_users[conn.getpeername()])
    if q == None:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["no_question"], "")
    else:
        client_question =q.split(chatlib.DATA_DELIMITER)[0]
        print(client_question)
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_question"], q)


def handle_answer_message(conn, username, data):
    [num_question, answer] = chatlib.split_data(data, 2)
    correct_answer = str(questions[num_question]["correct"])
    if num_question != client_question:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["No_cheating"], "")
    elif answer == correct_answer:
        users[username]["score"] += 5
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["correct_answer"], "")
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["wrong_answer"], correct_answer)


def main():
    # Initializes global users and questions dictionaries using load functions, will be used later
    global users
    global questions, messages_to_send

    print("Welcome to Trivia Server!")
    load_questions_from_web()
    load_user_database()
    server_socket = setup_socket()
    client_sockets_list = []
    client_sockets = []
    messages_to_send = []
    while True:
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:
                (client_socket, client_address) = current_socket.accept()
                print("New client joined!", client_address)
                client_sockets.append(client_socket)
                print_client_socket(client_sockets)
            else:
                try:
                    cmd, data = recv_message_and_parse(current_socket)
                    if cmd is None or cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
                        print("client logout" + str(current_socket.getpeername()))
                        client_sockets.remove(current_socket)
                        handle_logout_message(current_socket)
                    elif cmd in chatlib.PROTOCOL_CLIENT.values():
                        handle_client_message(current_socket, cmd, data)
                    else:
                        send_error(current_socket, "invalid cmd")
                        print("ERROR: client sent:", cmd, ":", data)
                except ConnectionResetError:
                    client_sockets.remove(current_socket)
                    handle_logout_message(current_socket)
            for message in messages_to_send:
                current_socket, data = message
                if current_socket in ready_to_write:
                    try:
                        current_socket.send(data)
                        messages_to_send.remove(message)
                    except ConnectionResetError:
                        print("user disconnected")
                        handle_logout_message(current_socket)


if __name__ == '__main__':
    main()
