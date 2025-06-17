
import subprocess
import sys


# Banner

# search for songs
def search_for_songs():
    result = subprocess.run(["yt-dlp", f"ytsearch:next phonk song", "--get-url"],
    stdout=subprocess.PIPE,
    text=True ,
    stderr=subprocess.PIPE
    )

# select one result & enter 

# play that song on terminal
def play_song():
    url = "https://rr1---sn-cnoa-jv3s.googlevideo.com/videoplayback?expire=1750183380&ei=dFlRaLbmDfWf4t4PveqIwAM&ip=117.231.179.244&id=o-AFWK79DWMjKCGD0VMX_irXuMBXSP3CfOat2RRT2BVwrf&itag=251&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&met=1750161780%2C&mh=wM&mm=31%2C29&mn=sn-cnoa-jv3s%2Csn-h557sn67&ms=au%2Crdu&mv=m&mvi=1&pcm2cms=yes&pl=20&rms=au%2Cau&initcwndbps=1733750&bui=AY1jyLMCk8z_rAxOcKvDTrbQfcSLwS_3F7feBiil7c5TkFihc9HZcanMBcu0cOfutDQK6dRYBpnln6kO&vprv=1&svpuc=1&mime=audio%2Fwebm&ns=wahhYJuwNJpCelVKD01p0zkQ&rqh=1&gir=yes&clen=1630905&dur=103.201&lmt=1738037690238044&mt=1750161417&fvip=1&keepalive=yes&lmw=1&c=TVHTML5&sefc=1&txp=4532534&n=h0Ge_hR26zDamQ&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cbui%2Cvprv%2Csvpuc%2Cmime%2Cns%2Crqh%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=met%2Cmh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpcm2cms%2Cpl%2Crms%2Cinitcwndbps&lsig=APaTxxMwRgIhAPSLZFbxJHidAAGNSH1bm5c4nHZjO_DGq2MYYsdzUD_iAiEAq9Dua_7tQNUWoLF5AVH7MJXpTvVXnxHBVZ7lSFXlbBc%3D&sig=AJfQdSswRQIhAOakCJ8IsDv32fyj2cx8aAVBXG_AEjkIe7_JqMXAo-gOAiB1M372e2_vDI-YIUxOUJFjI1TKyiCkfA_4lZkEEFF6Lg%3D%3D"

    subprocess.run(["mpv", "--no-video", url])
 

 

def main():
    print("welcome to yt-terminal")
    if len(sys.argv) < 2:
        print("usage: python yt-terminal.py <search-term>")
    else:
        print("ok")
    
    



if __name__ == "__main__":
    main();