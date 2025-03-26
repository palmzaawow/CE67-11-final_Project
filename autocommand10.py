import sys
import websocket
import json
import os
import subprocess  
import csv  
import spidev
import time
import shutil
import lgpio

# websocket -----------------------------------------------------------------------------

def on_open(ws): # open connection
    print("WebSocket connection opened.")
 
def on_error(ws, error):  # print error 
    print(f"Error: {error}")

def on_message(ws, message): # input message
    global h, receiving_input_csv, receiving_csv, receiving_bin, current_board, INPUT_PIN_A, INPUT_PIN_B
    
    if isinstance(message, bytes):

        print("Received binary message")
        if receiving_csv:  # case save file CSV                   # 3A  3B
            save_received_csv(message, current_board) 
        elif receiving_bin: # case save file bin                  # 6A  6B
            save_received_bin(current_board, message)  
        elif receiving_input_csv: # case save file input CSV   
            save_received_input_csv(message, current_board)       # 2.5A  2.5B
        # add here

    else:

        print(f"Received message from server: {message}")
        data = json.loads(message)

        # Check for board commands
        if data.get("command") == "upload_board_A":             # 1A
            current_board = "A"
            print("Received command to upload board A")
            receive_input_csv(ws)
            #receive_csv(ws)                                                    # add here

        elif data.get("command") == "upload_board_B":            # 1B
            current_board = "B"
            print("Received command to upload board B")
            receive_input_csv(ws)
            #receive_csv(ws)                                                    # add here
        
        # elif data.get("command") == "send_csv_board_A":                                  # 13A

        #     current_board = "A"

        #     directory = f"Board_{current_board}"

        #     if not os.path.exists(directory):
        #         os.makedirs(directory)

        #     filename = os.path.join(directory, "output_data_board_A.csv")
        #     print("send output file board A")

        #     send_csv(ws, filename)
        #     clear_folder(directory)

        #     current_board = None

        # elif data.get("command") == "send_csv_board_B":                                      # 13B

        #     current_board = "B"

        #     directory = f"Board_{current_board}"

        #     if not os.path.exists(directory):
        #         os.makedirs(directory)
                
        #     filename = os.path.join(directory, "output_data_board_B.csv")
        #     print("send output file board B")

        #     send_csv(ws, filename)
        #     clear_folder(directory)
            
        #     current_board = None

        elif data.get("command") == "spi_getdatacapture_board_A":                       # 11A
            current_board = "A"
            send_getdata_spi(current_board)
            send_csv_extra(current_board)
            current_board = None

        elif data.get("command") == "spi_getdatacapture_board_B":                        # 11B
            current_board = "B"
            send_getdata_spi(current_board)
            send_csv_extra(current_board)
            current_board = None
        
        elif data.get("command") == "check_status_board":    
            B_A = lgpio.gpio_read(h, INPUT_PIN_A)
            B_B = lgpio.gpio_read(h, INPUT_PIN_B)                
            print(f"broads A : {B_A},broads B : {B_B}")
            command = {"command":f"{B_A} : {B_B}"}                          
            ws.send(json.dumps(command))

def on_close(ws, close_status_code, close_msg):     # close connection
    print(f"WebSocket connection closed with code: {close_status_code}, message: {close_msg}")



# function ------------------------------------------------------------------------------------------

def send_csv(ws, filename):  # send CSV
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            file_data = file.read()
            ws.send(file_data, opcode=websocket.ABNF.OPCODE_BINARY)
            print(f"Sent CSV file: {filename}")
    else:
        print(f"File {filename} does not exist.")

def receive_csv(ws): # receive ready CSV
    global receiving_csv, receiving_bin, receiving_input_csv
    print("Ready to receive CSV file...")

    command = {"command": "ready_to_receive_csv"}                              # 2A  2B
    ws.send(json.dumps(command))

    receiving_csv = True  # Set flag to expect CSV
    receiving_bin = False  # Reset bin flag
    receiving_input_csv = False

    #   add here


def receive_input_csv(ws): # receive ready input CSV
    global receiving_csv, receiving_bin, receiving_input_csv
    print("Ready to receive input CSV file...")

    command = {"command": "ready_to_receive_input_csv"}                              # 
    ws.send(json.dumps(command))

    receiving_input_csv = True
    receiving_csv = False  # Set flag to expect CSV
    receiving_bin = False  # Reset bin flag

def send_csv_extra(current_board):
    global PIN_reset_A, PIN_reset_B

    directory = f"Board_{current_board}"

    if not os.path.exists(directory):
        os.makedirs(directory)
    if current_board == 'A':
        filename = os.path.join(directory, "output_data_board_A.csv")
        print("send output file board A")
    elif current_board == 'B':
        filename = os.path.join(directory, "output_data_board_B.csv")
        print("send output file board B")
    

    send_csv(ws, filename)
    clear_folder(directory)

    if current_board == 'A':
        lgpio.gpio_write(h, PIN_reset_A, 1)  
        time.sleep(0.5)                  
        lgpio.gpio_write(h, PIN_reset_A, 0)
        print("Reset board A")
    elif current_board == 'B':
        lgpio.gpio_write(h, PIN_reset_B, 1)  
        time.sleep(0.5)                  
        lgpio.gpio_write(h, PIN_reset_B, 0)
        print("Reset board B")
    #current_board = None



def save_received_csv(data, current_board): # save CSV
    print("Saving received CSV file...")

    # Create directory if it doesn't exist
    directory = f"Board_{current_board}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    if current_board == "A":                                                   #  4A
        filename = os.path.join(directory, "received_data_board_A.csv")
    elif current_board == "B":                                                 #  4B
        filename = os.path.join(directory, "received_data_board_B.csv")

    with open(filename, "wb") as file:
        file.write(data)
    print(f"CSV file saved as '{filename}'.")

    # After CSV is received, ready to receive bin
    receive_bin(ws)

    #  add here 

def save_received_input_csv(data, current_board): # save input CSV
    print("Saving received input CSV file...")

    # Create directory if it doesn't exist
    directory = f"Board_{current_board}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    if current_board == "A":                                                   #  
        filename = os.path.join(directory, "received_input_data_board_A.csv")
    elif current_board == "B":                                                 #  
        filename = os.path.join(directory, "received_input_data_board_B.csv")

    with open(filename, "wb") as file:
        file.write(data)
    print(f"CSV file saved as '{filename}'.")

    # After input CSV is received, ready to receive CSV
    receive_csv(ws)   



def receive_bin(ws): # receive ready Bin
    global receiving_csv, receiving_bin ,receiving_input_csv
    print("Ready to receive .bin file...")

    command = {"command": "ready_to_receive_bin"}                                 # 5A  5B
    ws.send(json.dumps(command))

    receiving_bin = True  # Set flag to expect bin
    receiving_csv = False  # Reset CSV flag
    receiving_input_csv = False

def save_received_bin(current_board, data): # save Bin
    print("Saving received .bin file...")

    # Create directory if it doesn't exist
    directory = f"Board_{current_board}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    if current_board == "A":                                                         # 7A
        filename = os.path.join(directory, "received_data_board_A.bin")
    elif current_board == "B":
        filename = os.path.join(directory, "received_data_board_B.bin")              # 7B

    with open(filename, "wb") as file:
        file.write(data)
    print(f".bin file saved as '{filename}'.")

    # Call function to flash the board after saving the .bin file
    flash_board(current_board, filename)
    # Call function to config the FPGA after saving the .bin file
    send_config_spi(current_board)

def flash_board(current_board, file_path): 

    if current_board == "A":
        board = "066BFF495157808667170732"  # Serial_board_A                          # 8A
    elif current_board == "B":
        board = "066EFF495257808667092216"  # Serial_board_B                          # 8B
    else:
        print("Unknown board.")
        return

    try:
        erase_command = f'st-flash --serial={board} erase'
        print(f"Running command: {erase_command}")
        subprocess.run(erase_command, shell=True, check=True)

        write_command = f'st-flash --serial={board} write {file_path} 0x08000000'
        print(f"Running command: {write_command}")
        subprocess.run(write_command, shell=True, check=True)

        print(f"Successfully flashed board {current_board}.")

        command = {"command": f"Successfully flashed board {current_board}"}
        ws.send(json.dumps(command))

    except subprocess.CalledProcessError as e:
        print(f"Error occurred during flashing: {e}")

        command = {"command": f"Error occurred during flashing board {current_board}: {e}"}
        ws.send(json.dumps(command))

def readcsv(file_path): 
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            csv_reader = csv.reader(csvfile)
            output = ""
            for row in csv_reader:
                if row:  
                    type, pin, edge = row
                    message = f"Type: {type}, Pin: {pin}, Edge: {edge}"
                    print(f"Extracted data: {message}")
                    
                    if type.strip()  == "GPIO":  #.strip() 
                        output += f"G{pin}"
                    elif type.strip()  == "PWM": #.strip()
                        output += f"P{pin}"
            print(len(output))
            check = len(output)//2
            if len(output) < 16:
                output += "G9" * (8 - (len(output) // 2))  
            
            return output, check
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

def read_inputcsv(file_path): 
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            csv_reader = csv.reader(csvfile)
            output_pin1 = ""
            output_pin2 = ""
            counter_pin1 = 0
            counter_pin2 = 0
            for row in csv_reader:
                if row:  
                    type1, pin1, value1, time1, type2, pin2, value2, time2 = row
                    message = f"Type1: {type1}, Pin1: {pin1}, Value1: {value1}, Time1: {time1}, Type2: {type2}, Pin2: {pin2}, Value2: {value2}, Time2: {time2}"
                    # print(f"Extracted data: {message}")
                    setpin1 = ""
                    setpin2 = ""
                    if type1 and pin1 and value1 and time1:
                        if type1 == "ee" and pin1 == "ee" and value1 == "ee" and time1 == "ee":
                            # print("datapin1 ไม่มีข้อมูล")
                            setpin1 += "1000000000000000"
                            counter_pin1 += 1

                        else:# print("datapin1 มีข้อมูล")
                            if type1.strip() == "GPIO":
                                setpin1 += '0'
                            setpin1 += str(int(pin1)-1)
                            setpin1 += value1
                            time1data = int(float(time1)*1000)
                            time1_13_bit = format(time1data, '013b')
                            setpin1 += str(time1_13_bit)

                            counter_pin1 += 1
                    
                        
                        

                    if type2 and pin2 and value2 and time2:
                        if type1 == "ee" and pin1 == "ee" and value1 == "ee" and time1 == "ee":
                             # print("datapin2 ไม่มีข้อมูล")
                            setpin2 += "1100000000000000"

                            counter_pin2 += 1

                        else :
                            # print("datapin2 มีข้อมูล")
                            if type2.strip() == "GPIO":
                                setpin2 += '0'
                            setpin2 += str(int(pin2)-1)
                            setpin2 += value2
                            time2data = int(float(time2)*1000)
                            time2_13_bit = format(time2data, '013b')
                            setpin2 += str(time2_13_bit)

                            counter_pin2 += 1
                  
                    
                    output_pin1 += setpin1
                    # output_pin1 += " "
                    output_pin2 += setpin2
                    # output_pin2 += " "

            print(f"count1 : {counter_pin1}, count2 : {counter_pin2}")

            if counter_pin1 < 20:
                output_pin1 += "1000000000000000" * (20-counter_pin1)
            
            if counter_pin2 < 20:
                output_pin2 += "1100000000000000" * (20-counter_pin2)

            output_all = output_pin1 + output_pin2

            return output_all
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

#SPi -----------------------------------------------------------------------------

def init_spi(bus=0, device=0, max_speed=100000, mode=0b00):
    spi = spidev.SpiDev()
    spi.open(bus, device)
    spi.max_speed_hz = max_speed
    spi.mode = mode
    return spi

def spi_transfer(spi, data):
    response = spi.xfer2(data)
    return response

def send_data_in_16bit_frames(spi, data, num_times):
    bytes_data = data.encode('utf-8') 
    frame_size = 2  
    last_response = None

    for _ in range(num_times):
        print(f"Sending data: {data}")

        for i in range(0, len(bytes_data), frame_size):
            frame = bytes_data[i:i+frame_size]
       
            if len(frame) < frame_size:
                frame += b' '  
            
            response = spi_transfer(spi, list(frame))
            hex_response = ''.join(format(b, '02x') for b in response)
            print(f"Sent frame: {frame}, Received response: {hex_response}")
            
            last_response = response 

    return last_response

def send_inputdata_in_16bit_frames(spi, data_bits, num_times):
    frame_size = 16 
    last_response = None

    if len(data_bits) % frame_size != 0:
        print("Data length is not a multiple of 16 bits")
        return None

    for _ in range(num_times):
        print(f"Sending data: {data_bits}")

        for i in range(0, len(data_bits), frame_size):
            frame = data_bits[i:i+frame_size]  

            frame_bytes = [int(frame[j:j+8], 2) for j in range(0, frame_size, 8)]
            
            response = spi_transfer(spi, frame_bytes) 
            hex_response = ''.join(format(b, '02x') for b in response)
            print(f"Sent frame: {frame}, Received response: {hex_response}")
            
            last_response = response 

    return last_response

def send_config_spi(current_board):                                                                                                               
    global h, GPIO_RSTPIN_A, GPIO_RSTPIN_B, pin_check_A, pin_check_B

    if current_board == "A":                                                                                 # 9A
        
        spi_G = init_spi(bus=0, device=0, max_speed=100000, mode=0b00)
    elif current_board == "B":                                                                               # 9B

        spi_G = init_spi(bus=0, device=1, max_speed=100000, mode=0b00)

    print(f"Start config FPGA")

    directory = f"Board_{current_board}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        final_response = send_data_in_16bit_frames(spi_G, "st", num_times=3)

        final_hex_response = ''.join(format(b, '02x') for b in final_response)
        print(f"Final response : {final_hex_response}") # 3032

        
        if final_hex_response == '3032':
            if current_board == "A":
                filename = os.path.join(directory, "received_data_board_A.csv")
                configpin, pin_check_A = readcsv(filename)
                inputfilename = os.path.join(directory, "received_input_data_board_A.csv")
                configinput = read_inputcsv(inputfilename)
            elif current_board == "B":
                filename = os.path.join(directory, "received_data_board_B.csv")
                configpin, pin_check_B = readcsv(filename)
                inputfilename = os.path.join(directory, "received_input_data_board_B.csv")
                configinput = read_inputcsv(inputfilename)

            print(configpin)
            print(f"leninput : {len(configinput)}")
            print(configinput)

            configpin_response = send_data_in_16bit_frames(spi_G, configpin, num_times=1)             # change here                                     # change here
            print("config output success")
            configpin_response = send_inputdata_in_16bit_frames(spi_G, configinput, num_times=1)      # add here
            print("config input success")
            
            configpin_response = send_data_in_16bit_frames(spi_G, "ss", num_times=28)
            
            config_hex_response = ''.join(format(b, '02x') for b in configpin_response)
            print(f"Final response : {config_hex_response}") # cm

            

            if config_hex_response == '636d':     #cm 636d
                spi_G.close()
                print(f"Finish config FPGA")
                if current_board == "A":
                    #hw reset pin A
                    print("reset_board_A")
                    lgpio.gpio_write(h, GPIO_RSTPIN_A, 1)  
                    time.sleep(0.5)                  
                    lgpio.gpio_write(h, GPIO_RSTPIN_A, 0)
                    print("start_capture")
                    command = {"command": f"Successfully config board {current_board} start capture"}                                    # 10A
                    ws.send(json.dumps(command))

                elif current_board == "B":
                    #hw reset pin B
                    lgpio.gpio_write(h, GPIO_RSTPIN_B, 1)  
                    time.sleep(0.5)                  
                    lgpio.gpio_write(h, GPIO_RSTPIN_B, 0)

                    command = {"command": f"Successfully config board {current_board} start capture"}                                    # 10B
                    ws.send(json.dumps(command))
                

    except Exception as e:
        spi_G.close()
        print(f"An error occurred: {e}")

# config ------------------------------------------------------------------------------------------

def send_getdata_spi(current_board):
    global pin_check_A, pin_check_B
    
    if current_board == "A":                                                                                 #  12A
        spi_G = init_spi(bus=0, device=0, max_speed=100000, mode=0b00)
    elif current_board == "B":                                                                               #  12B
        spi_G = init_spi(bus=0, device=1, max_speed=100000, mode=0b00)

    print(f"Start getdata from FPGA")

    pin_use = 0

    directory = f"Board_{current_board}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    if current_board == "A":
        filename = os.path.join(directory, "output_data_board_A.csv")
        pin_use = pin_check_A

    elif current_board == "B":
        filename = os.path.join(directory, "output_data_board_B.csv")
        pin_use = pin_check_B

    with open(filename, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)

        collected_data = "" 
        buffered_pins = [] 
        row_csv = 0

        try:
            while True:
                
                print("Sending 'rs' to FPGA...")
                response = send_data_in_16bit_frames(spi_G, "re", num_times=1)  

                if response:  
                    
                    bit_response = ''.join(format(b, '08b') for b in response)  
                    print(f"Received response (bit): {bit_response}")          # show data in bit

                    hex_response = ''.join(format(b, '02x') for b in response)  
                    print(f"Received response (hex): {hex_response}")          # show data in hex

                    if hex_response == '726a':  # "rj" 
                        print("Received 'rj'. Stopping data collection.")
                        response = send_data_in_16bit_frames(spi_G, "00", num_times=1) 
                        spi_G.close()
                        break
                    if hex_response != '636d'and hex_response != 'ffff':
                        collected_data += bit_response

                    if len(collected_data) >= 32:                                    # change here
                        row_data = collected_data[:32]  
                        collected_data = collected_data[32:]  

                        
                        type_bits = row_data[:1]   # 1 bit
                        pin_bits = row_data[1:4]    # 3  bit
                        value_bits = row_data[4:16]  #  12 bit
                        timestamp_bits = row_data[16:32]  # 16 bit
                        
                        value_bits = value_bits.strip()
                        timestamp_bits = timestamp_bits.strip()
                        
                        type_value = int(type_bits, 2)
                        pin_value = int(pin_bits, 2)
                        val = int(value_bits, 2)
                        print(val)
                        if val >= 1:
                            value = 1
                        else:
                            value = 0
                        #value = int(value_bits, 2)
                        timestamp = int(timestamp_bits, 2)

                        print(f"type : {type_value}")
                        print(f"pin : {pin_value}")
                        print(f"value : {value}")
                        print(f"time : {timestamp}")
                        
                        #if type_value < 2 and pin_value < 9 and value < 2 and timestamp < 8192:
                        buffered_pins.append((type_value, pin_value, value, timestamp))
                        #buzfered_pins.append((type_bits, pin_bits, value_bits, timestamp_bits))

                        if len(buffered_pins) == pin_use and row_csv < 40:
                            flat_row = [item for pin_data in buffered_pins for item in pin_data]  
                            csv_writer.writerow(flat_row)
                            row_csv += 1
                            print(f"Wrote to CSV: {flat_row}")
                            buffered_pins = []

                        #csv_writer.writerow([type_value, pin_value, value, timestamp]) #write to csv
                        #print(f"Wrote to CSV: {type_value}, {pin_value}, {value}, {timestamp}")

        except Exception as e:
            spi_G.close()
            print(f"An error occurred: {e}")

    print(f"Finished writing data to {filename}.")

    #command = {"command": f"Successfully get data Capture from board {current_board}"}
    #ws.send(json.dumps(command))


def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)  
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"Deleted folder: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

if __name__ == "__main__":
    receiving_csv = False  # Initialize flag for receiving CSV
    receiving_bin = False  # Initialize flag for receiving bin
    receiving_input_csv = False # Initialize flag for receiving input CSV
    current_board = None   # To track which board is being used
    pin_check_A = 0
    pin_check_B = 0

    GPIO_RSTPIN_A = 17
    GPIO_RSTPIN_B = 18
    INPUT_PIN_A = 23 
    INPUT_PIN_B = 24 

    PIN_reset_A = 3
    PIN_reset_B = 4

    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(h, GPIO_RSTPIN_A)
    lgpio.gpio_claim_output(h, GPIO_RSTPIN_B)
    lgpio.gpio_claim_output(h, PIN_reset_A)
    lgpio.gpio_claim_output(h, PIN_reset_B)
    lgpio.gpio_claim_input(h, INPUT_PIN_A)
    lgpio.gpio_claim_input(h, INPUT_PIN_B)

    lgpio.gpio_write(h, GPIO_RSTPIN_A, 0)
    lgpio.gpio_write(h, GPIO_RSTPIN_B, 0)

    lgpio.gpio_write(h, PIN_reset_A, 1)  
    lgpio.gpio_write(h, PIN_reset_B, 1)  
    time.sleep(0.5)                
    lgpio.gpio_write(h, PIN_reset_A, 0)    
    lgpio.gpio_write(h, PIN_reset_B, 0)

    lgpio.gpio_write(h, PIN_reset_A, 0)
    lgpio.gpio_write(h, PIN_reset_B, 0)

    ws = websocket.WebSocketApp("wss://uncommon-worthy-bluebird.ngrok-free.app/ws",  
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()
