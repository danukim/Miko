import os
import time
import requests
from huggingface_hub import snapshot_download

print(
    """
  _____              ______             _ _           
 / ___ \            (_____ \           | (_)_         
| |   | |____   ____ _____) ) ____ ____| |_| |_ _   _ 
| |   | |  _ \ / _  |_____ ( / _  ) _  | | |  _) | | |
| |___| | | | ( (/ /      | ( (/ ( ( | | | | |_| |_| |
 \_____/|_| |_|\____)     |_|\____)_||_|_|_|\___)__  |
                                               (____/
"""
)


def typewriter_effect(text, delay=0.03):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)


text = """        Bridging the real and virtual worlds
{:^50}
""".format(
    "[PROJECT MIKO Install Script]"
)

typewriter_effect(text)

cmd = os.system
cmd("python -m pip install pipenv")
print("Only Windows + Nvidia has been officially tested. Linux + Nvidia should work, but it is untested. Mac and other GPUs are not currently supported. Would you like to continue? [y/n]")
w = input()
if w == "y":
    print("Okay, installing pytorch...")
    cmd("python -m pipenv run pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
else:
    exit()
print("Installing hugging-face-hub...")
cmd("python -m pip install huggingface-hub")

print("Installing dependencies...")
cmd("pipenv install --ignore-pipfile")

print('''Now please enter the ID (simply owner/name; e.g. TheBloke/dolphin-2.1-mistral-7B-GPTQ) of the GPTQ model on huggingface you want to download. If you don't know what this is, just answer "d" and the default model 
dolphin-2.1-mistral-7B-GPTQ  will be downloaded.''')
x = input("ID: ")
y = input(r"Directory to download to; e.g. C:\Users\username\Downloads: ")
if x == "d":
    snapshot_download(repo_id="TheBloke/dolphin-2.1-mistral-7B-GPTQ", local_dir=fr"{y}", local_dir_use_symlinks=False)
    llm_path = fr"{y} + \dolphin-2.1-mistral-7B-GPTQ"
else:
    index = x.find('/')
    if index != -1:
        x = x[index + 1:]
    else:
        x = x
    snapshot_download(repo_id=x, local_dir=fr"{y}\{x}", local_dir_use_symlinks=False)
    llm_path = y

# URL of the file to download
url = "https://huggingface.co/DogeLord/megumin-VITS/resolve/main/G_latest.pth"

# Define the local filename where you want to save the downloaded file
local_filename = "G_latest.pth"

# Send a GET request to the URL
response = requests.get(url, stream=True)

# Check if the request was successful (HTTP status code 200)
if response.status_code == 200:
    # Open a local file for binary writing
    print("Downloading TTS model...")
    with open(r"vits-simple-api-onereality/Model/g/" + local_filename, 'wb') as file:
        # Iterate over the content in chunks and write it to the local file
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print(f"Downloaded {local_filename}")
else:
    print(f"Failed to download the file. HTTP status code: {response.status_code}")

print("Do you want to use tuya? (Basically smart home control with the AI but a bit complicated to set up. Check the prerequisites on my README on my Github.) [y/n]")
t = input()
if t == "n":
    print("Okay, Removing tuya from script...")
    with open ("OneRealityMemory.py", "r") as f:
        data = f.read()
        data = data.replace("tuya = True", "tuya = False")
    with open ("OneRealityMemory.py", "w") as f:
        f.write(data)
else:
    print("Okay, continuing...")
    
print("If you ever change your mind about any of these options, please edit the .env file!")
print("Note if you encounter any errors when running OneReality.bat, please read the error, it might say install this or that. if you can't figure it out, please contact me on discord: https://discord.gg/PN48PZEXJS")


print("Would you like to go through the setup here or just exit? ONLY RUN THIS ONCE! [y/n]")
print("If you want to change anything after this, again, please edit the .env file!")
if input() == "y":
    print("Okay, continuing...")
else:
    exit()

print("Leave any blank if you want to use the default value")
print("--------------------")
print("Supported languages are: English, 한국어, 日本語, or 简体中文. Default is English")
language = input("Language: ")
print("--------------------")
print("What is your name? Default is User")
name = input("Name: ")
print("--------------------")
print("What WhisperX model do you want to use? Options are tiny, base, small, medium, large, and large-v2. Default is large-v2")
whisperx = input("Model: ")
print("--------------------")
if t != "n":
    print("Go here: https://iot.tuya.com/cloud/basic Access ID/Client ID is TUYA_ID and Access Secret/Client Secret is TUYA_SECRET")
    tuya_id = input("TUYA_ID: ")
    tuya_secret = input("TUYA_SECRET: ")
    print("In the link above, take note of the datacenter location and in this link: https://developer.tuya.com/en/docs/iot/api-request?id=Ka4a8uuo1j4t4#title-1-Endpoints find the corresponding endpoint link. Default is US West, https://openapi.tuyaus.com")
    endpoint = input("Endpoint link: ")
    if endpoint == "":
        endpoint = "https://openapi.tuyaus.com"
    print("--------------------")
    print("Enter the name of the first device you want to control. Something easy to remember because this is what you will say to the AI")
    device_1 = input("Device name: ")
    print("Now enter the ID of the first device you want to control. You'll find this here: https://us.iot.tuya.com/cloud/basic?toptab=related&deviceTab=all")
    device_1_id = input("Device ID: ")
else:
    pass

print("To add Tuya devices, please edit the .env file!")
print("Also, to add apps Miko can open, just edit line 274 in OneRealityMemory.py!")

# Now we need to write the data to the env file
with open(".env", "r") as f:
    data = f.read()
    data = data.replace("English", language)
    data = data.replace("User", name)
    data = data.replace("large-v2", whisperx)
    data = data.replace("llm_path", llm_path)
    data = data.replace("large-v2", whisperx)
    if t != "n":
        data = data.replace("tuya_id", tuya_id)
        data = data.replace("tuya_secret", tuya_secret)
        data = data.replace("https://openapi.tuyaus.com", endpoint)
        data = data.replace("DEVICE_1", device_1)
        data = data.replace("DEVICE_1_ID", device_1_id)
        
with open(".env", "w") as f:
    f.write(data)
    
print("SETUP COMPLETE! If you need help configuring how to control the samrt devices, hit me up on discord. https://discord.gg/PN48PZEXJS. Thanks for using OneReality: PROJECT MIKO!")