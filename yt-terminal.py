
import subprocess
import sys
import shutil
import threading


#colors # Use colorama (for better Windows support)
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

class Styles:
    italic = '\033[3m'
    normal = '\033[0m'

#move up a line and clean that line
# def moveup_and_clean_line(times, terminal_width):
#     for i in range(times):  
#         sys.stdout.write('\r' + ' ' * terminal_width + '\r')
#         sys.stdout.write('\033[F')
#         sys.stdout.write('\r' + ' ' * terminal_width + '\r')

#     # end if

    
# search for a song using yt-dlp
def search_for_songs(query, terminal_width):
    try:      
        result = subprocess.run(["yt-dlp", f"ytsearch1:{query} song","-f", "bestaudio", "--get-url", "--get-title"],
        stdout=subprocess.PIPE, # out
        text=True ,
        stderr=subprocess.PIPE #error
        )
        data = result.stdout.strip().splitlines()
        url = data[1]
        song_title = data[0]

        if (result.returncode == 0):
            sys.stdout.write('\033[F') # cursor moves up
        
            print(f"{Colors.CYAN}{Styles.normal}playing: {Colors.BLUE}{Styles.italic}{song_title}")
            print(f"{Colors.CYAN}{Styles.italic}{"press 'enter' to quit-song/search-new-song".center(terminal_width)}")
        else:
            print(f"{Colors.RED}nothing found! search again.{Colors.RED}")
 
        return url 
    
    except FileNotFoundError as e:
        print(f"{e}")
        print("please install yt-dlp in your system.")
        # TODO: auto install yt-dlp
        sys.exit(1)
    except Exception:
        print(f"{Colors.RED}{result.stderr}{Colors.RED}")
 


# play song using mpv
def play_song(url, terminal_width):
    try:
        # play song using mpv
        process = subprocess.Popen(["mpv", "--no-video", url])

        def listen_for_enterkey():
            while (True):
                key = input()
                if key == '':
                    process.terminate()
                    break
                    break                
                # end if 
            # end while
        input_thread = threading.Thread(target=listen_for_enterkey(), daemon=True)
        input_thread.start()
        process.wait()
         
    except FileNotFoundError as e:
        print(f"{e}")
        print("please install mpv in your system.")
        # TODO: auto install mpv
        sys.exit(1)
 
 

 

def main():
    # banner
    print(Colors.BLUE + r"""
           _             _                      _             _ 
 _   _| |_          | |_ ___ _ __ _ __ ___ (_)_ __   __ _| |
| | | | __|  _____  | __/ _ \ '__| '_ ` _ \| | '_ \ / _` | |
| |_| | |_  |_____| | ||  __/ |  | | | | | | | | | | (_| | |
 \__, |\__|          \__\___|_|  |_| |_| |_|_|_| |_|\__,_|_|
 |___/   

                made by kai1ax
     """ + Colors.BLUE)


    terminal_width = shutil.get_terminal_size().columns
    while (True):
        #user input:
        query = input(f"{Colors.CYAN}search any song: ")
        if (query == ""):
            sys.stdout.write('\033[F') # ensures always on same line
            continue
        # if there is a input
        sys.stdout.write("\033[F")  #move cursor up one line
        sys.stdout.flush()
        print(f"{Colors.CYAN}searching for:{Colors.BLUE} {query} .....")
        
        
        url = search_for_songs(query, terminal_width)
        play_song(url, terminal_width)
    # end while



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{Colors.YELLOW}Exiting yt-terminal, bye bye...{Colors.YELLOW}")
        sys.exit(0)