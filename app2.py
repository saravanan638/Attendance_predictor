from flask import Flask, request, render_template
import os
from PIL import Image
import google.generativeai as genai
import json
import re
genai.configure(api_key="AIzaSyB5-60LnkS-NV0qdj_x_emLSwPVqIGGwr4")
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
  generation_config=generation_config,
)


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def upload_to_genai(path, mime_type=None):
   
    file = genai.upload_file(path, mime_type=mime_type)
    return file

@app.route("/", methods=["GET", "POST"])
def index():
    output_text = None
    if request.method == "POST":
        if "image" not in request.files or not all(key in request.form for key in ["hours_per_day", "leave_days", "deadline_percentage"]):
            return render_template("index2.html", output_text="Incomplete input. Please provide all required data.")

        
        file = request.files["image"]
        tot_hrs_per_day = int(request.form.get("hours_per_day"))
        leave = int(request.form.get("leave_days"))
        deadline = int(request.form.get("deadline_percentage"))

        if file:
            try:
            
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(file_path)
                image = Image.open(file_path).convert("RGB")

                
                uploaded_file = upload_to_genai(file_path, mime_type="image/png")

                
                response = model.generate_content([
                    uploaded_file,
                    "Extract the subject name, maximum hours, and attended hours from the table in the image, and output as a JSON array with keys: subject, max_hours, and attended_hours.."
                ])

                
                json_string = response.text
                match = re.search(r'\[.*\]', json_string, re.DOTALL)
                if match:
                    valid_json_string = match.group()
                    data = json.loads(valid_json_string)
                    subjects=[]
                    max_hrs= []
                    attended_hrs=[]
                    
                    for item in data:
                        subjects.append(item["subject"])
                        max_hrs.append(item["max_hours"])
                        attended_hrs.append(item["attended_hours"])
                    tot_hrs_attend=sum(attended_hrs)
                    tot_hrs=sum(max_hrs)
                    cur_percent = (tot_hrs_attend / tot_hrs) * 100
                    cur_percent = round(cur_percent, 3)
                    if leave >= 1:
                        tot_hrs += leave
                        exact_percent = (tot_hrs_attend / tot_hrs) * 100
                        exact_percent = round(exact_percent, 3)
                    else:
                        exact_percent = cur_percent
                    i = 0
                    exact_percent1=exact_percent
                    while exact_percent1 < deadline:
                        tot_hrs += tot_hrs_per_day
                        tot_hrs_attend += tot_hrs_per_day
                        exact_percent1 = (tot_hrs_attend / tot_hrs) * 100
                        i += 1
                    if exact_percent1 >= deadline:
                        target_days = i
                    else:
                        target_days = 0
                    if target_days == 0: 
                        conclusion = "You Are Safe. Congrats And Keep Going!"
                    else:
                        conclusion = "You Are Not Safe. Please Attend The Classes."
                    output_text = f"\nCurrent Percentage: {cur_percent}% \n Exact Percent After Leave : {exact_percent}% \n No.Of Days Need To Attend The Regular Class : {target_days} \n Conclusion : {conclusion}"   
                    
                else:
                    output_text = "You Are Uploaded An Unwanted Image. Please Enter Your Attendace Screenshot."

            except Exception as e:
                output_text = f"Error: {e}"

    return render_template("index2.html", output_text=output_text)

if __name__ == "__main__":
    app.run(debug=False,port=8000)
