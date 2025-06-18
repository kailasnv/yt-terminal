
import subprocess
import sys



 

#colors # Use colorama (for better Windows support)
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    
# search for a song using yt-dlp
def search_for_songs(query):
    try:      
        result = subprocess.run(["yt-dlp", f"ytsearch1:{query}","-f", "bestaudio", "--get-url"],
        stdout=subprocess.PIPE, # out
        text=True ,
        stderr=subprocess.PIPE #error
        )
        if (result.returncode == 0):
            print(f"{Colors.GREEN}search success{Colors.GREEN}")
        else:
            print(f"{Colors.RED}nothing found! search again.{Colors.RED}")
             
        return result.stdout.strip()
    
    except FileNotFoundError as e:
        print(f"{e}")
        print("please install yt-dlp in your system.")
        # TODO: auto install yt-dlp
        sys.exit(1)
 



# play song using mpv
def play_song(url):
    try:
        # play song using mpv
        subprocess.run(["mpv", "--no-video", url])
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


    if len(sys.argv) < 2:
        print(f"{Colors.YELLOW}usage: python yt-terminal.py <search-term>{Colors.YELLOW}")
        sys.exit(1)
    #print(sys.argv[1:]) if there is a search term
    query = "".join(sys.argv[1:])
    print(f"Searching for: {query}")
    url = search_for_songs(query)
    # print(url)
    play_song(url)



if __name__ == "__main__":
    main();