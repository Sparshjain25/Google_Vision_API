import requests
import base64
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import os
import sys
import subprocess

def setup_environment(package_name):
    
    for package in package_name:
        try:
            # Checking the installed packages 
            subprocess.run([sys.executable, "-m", "pip", "show", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"{package} is already installed.")
        except subprocess.CalledProcessError:
            # Installing packages which are not installed.
            print(f"{package} is not installed. Installing...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"{package} installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Error: Installation of {package} failed - {e}")
                sys.exit(1)

def scan_objects(image_path):

    try: 
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode()

        api_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        
        request_body = {
            "requests": [
                {
                    "image": {"content": image_data},
                    "features": [{"type": "OBJECT_LOCALIZATION"},{"type": "WEB_DETECTION"}],
                }]}

        # Sending POST request  
        # response = requests.post(api_url, json=request_body, timeout=5)   ##Can add time constraint here in timeout for 5 sec for production to handle surplus requests.
        response = requests.post(api_url, json=request_body)
        response.raise_for_status()
        response_json = response.json()
        #print(response_json["responses"])


        # Extracting all the objects and image info from response
        if "responses" in response_json and len(response_json["responses"]) > 0 and len(response_json["responses"][0])>0:

            objects = []     #Objects Lists
            if "localizedObjectAnnotations" in response_json["responses"][0]:
                localization_data = response_json["responses"][0]["localizedObjectAnnotations"]
                for obj in localization_data:
                    name = obj["name"]   #Name of the object
                    score=obj["score"]   #Confidence of OCR tool for the particular object
                    bounding_box = obj["boundingPoly"]["normalizedVertices"]   #Location of the object detected in the image.
                    objects.append({"name": name, "score":score, "bounding_box": bounding_box})
            else:
                print("JSON repsonse for the Error:", response_json["responses"])
                objects.append(-1)   # To keep a check if unwanted response is received.
            

            Webs=[]   # Webs URL Lists showing similar images on the internet.
            # if "responses" in response_json and len(response_json["responses"]) > 0 and len(response_json["responses"][0])>0:
            if "webDetection" in response_json["responses"][0]:
                webs_data=response_json["responses"][0]["webDetection"]["visuallySimilarImages"]
                for url in webs_data:
                    Webs.append(url["url"])
            else:
                Webs.append(-1)
                print("Websites not found!!")
                
        else:
            objects.append(-1)  # To keep a check if no objects are detected.   
            Webs.append(-1)  

        return objects,Webs
    
    except FileNotFoundError:
        print("Error: Image file not found!!!!!!")
        return None,None
    except requests.exceptions.RequestException as e:
        print("***********Error sending request:************ \n CHECK INTERNET CONNECTION.....\n", e)
        return None,None

def show_webs(Webs):
    if len(Webs)>0:
        for i in range(len(Webs)):
            print("Link ",i,": ", Webs[i])

def show_objects(image_path, objects):
    
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Outling the objects detected in the image
    i=0   #Checker to count the objects
    for obj in objects:
        bounding_box = obj["bounding_box"]
        score=obj["score"]

        if (len(bounding_box)==4) and (len(bounding_box[0])==2) and (len(bounding_box[2])==2): #Checking objects with valid coordinates
            i=i+1   #Increasing the count only when the object has valid location.
            width, height = image.size
            x0 = int(bounding_box[0]['x'] * width)   #converting to int because better for acurate calculation further if needed...usually better results
            y0 = int(bounding_box[0]['y'] * height)
            x1 = int(bounding_box[2]['x'] * width)
            y1 = int(bounding_box[2]['y'] * height)

            draw.rectangle([x0, y0, x1, y1], outline="blue", width= int(score* 4))    #To vary the border of the box according to the confidence of the model.
            draw.text((x0, y0), obj["name"], fill="red")
    print("Total Number of Objects Detected: ",i)
    image.save('result.jpg')
    image.show()  



if __name__ == "__main__":

    package_name=["python-dotenv","Pillow","requests"]  #Add your packages here.
    setup_environment(package_name)

    image_path = "4.jpeg"
    load_dotenv("API_KEY.env")
    api_key = os.getenv("API_key")

    ext = [".jpg", ".jpeg", ".png"]     #Checking images with particular extensions only. Could have created another function for it.
    b, extension = os.path.splitext(image_path)

    if extension not in ext:
        print("Not Valid Image Extension")
    else:
        Objs,Webs = scan_objects(image_path)
        if Objs != None and Objs[0] != -1:
            show_objects(image_path, Objs)
        else:
            print("No objects detected by Google Vision API")
        if Webs != None and Webs[0] != -1:
            show_webs(Webs)
        else:
            print("No Websites found!!")
