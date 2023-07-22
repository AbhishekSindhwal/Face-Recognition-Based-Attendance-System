import pymongo
from datetime import datetime
from datetime import date
from datetime import timedelta
import streamlit as st
import face_recognition
import numpy as np
import cv2
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

if __name__=="__main__":

    #setting our page layout  
    st.set_page_config(layout="wide")
    
    st.title("Face Recognition Based Attendence System")

    #Dividing our page into two equal columns
    col1,col2=st.columns(2)

    now = datetime.now()
    current_date=now.strftime("%Y-%m-%d")

    #Connecting our python code to mongodb database
    client = pymongo.MongoClient(os.getenv('KEY'))

    #db variable reall_present_students student database
    db=client['student']

    #collection variable reall_present_students student database
    collection=db['names']
    

    #all variable contains data of names collection
    all=collection.find()
    
    all_student_face_encoding=[]
    all_student_name=[]
    all_present_student={'Name':[],'Time':[]}
    total_student=0

    for i in all:
        total_student+=1
        if current_date not in i:
            collection.update_one({"name":i['name']},{"$set":{current_date:'A'}})
            st.experimental_rerun()
        

        if i[current_date] =='P':
            current_time=now.strftime("%H hr-%M min")
            all_present_student['Name'].append(i['name'])
            all_present_student['Time'].append(current_time)

        all_student_name.append(i['name'])
        # total_student_list.append(i['name'])
        all_student_face_encoding.append(np.asarray(i['encoding'],dtype=np.float64))


    # all_student_face_encoding=np.ndarray(all_student_face_encoding1)
    # print(type(all_student_face_encoding))

    col1.write("Total number of student in our database: "+str(total_student))
    
    selected_mode_col1=col1.selectbox(
        "Select a mode",['Today Attendence','Student Attendence','List of Student']
    )

    #When we want to see today's attendence
    if selected_mode_col1=='Today Attendence':
        #Displaying today's attendence
        col1.dataframe(all_present_student,1000)


    #When we want to see past 5 attendence of every student
    if selected_mode_col1=='Student Attendence':
        today=date.today()
        student_list={'Name':[],str(today):[],str(today-timedelta(days=1)):[],str(today-timedelta(days=2)):[],str(today-timedelta(days=3)):[],
        str(today-timedelta(days=4)):[],str(today-timedelta(days=5)):[]}
        
        #Fetching the data of collection variable which denotes the collection name
        total=collection.find()

        #Traversing 
        for i in total:
            j=0
            student_list['Name'].append(i['name'])
            while j<6:
                # print(today-timedelta(days=j))
                if str(today-timedelta(days=j)) not in i:
                    student_list[str(today-timedelta(days=j))].append('NA')
                else: 
                    # print(i[str(today-timedelta(days=j))])
                    student_list[str(today-timedelta(days=j))].append(i[str(today-timedelta(days=j))])
                j+=1

        #Displaying the last 5 days attendence
        col1.dataframe(student_list,1000)


    #When we want to see list of students            
    if selected_mode_col1=='List of Student':
        total=collection.find()
        student_list={'Name':[]}

        for i in total:
            student_list['Name'].append(i['name'])

        #Displaying the list of student
        col1.dataframe(student_list,1000)


    selected_mode = col2.selectbox(
    	"Select a mode",['Mark Your Attendence','Create New User']
	)

    #When user select Create New User Mode 
    if selected_mode=='Create New User':
        username=col2.text_input("Enter Your Name")
        userpassword=col2.text_input("Enter Your password")
        pic1=col2.camera_input("Take a pictue")

        if pic1 is not None:
            b=pic1.getvalue()
            cimg=cv2.imdecode(np.frombuffer(b,np.uint8),cv2.IMREAD_COLOR)

            #By default uses HOG Algorithm (Histogram of Oriented Gradients)
            face_location=face_recognition.face_locations(cimg)
            if(len(face_location)<1):
                st.warning("There is no person in the image")
                st.experimental_rerun()
            face_encodings=face_recognition.face_encodings(cimg,face_location)
            
            if col2.button("Create User"):
                for face_encoding in face_encodings:
                    collection.insert_one({'name':username,'password':userpassword,'encoding':face_encoding.tolist(),current_date:'A'})
                st.balloons()
                st.warning("User is created !")


    #When User select Mark Your Attendence Mode
    if selected_mode=='Mark Your Attendence':
        pic=col2.camera_input("Take a pictue")
        if pic is not None:
            b=pic.getvalue()
            cimg=cv2.imdecode(np.frombuffer(b,np.uint8),cv2.IMREAD_COLOR)

            #It defaulty uses HOG Algorithm (Histogram of Oriented Gradients)
            face_location=face_recognition.face_locations(cimg)
            face_encodings=face_recognition.face_encodings(cimg,face_location)
            
            name=""
            flag=False

            #Checking All faces which is in the picture
            for face_encoding in face_encodings:
                matches=face_recognition.compare_faces(all_student_face_encoding,face_encoding)
                face_distance=face_recognition.face_distance(all_student_face_encoding,face_encoding)
                best_match_index=np.argmin(face_distance)
                print(best_match_index)
                if matches[best_match_index]:
                    name=all_student_name[best_match_index]
                    flag=True

                print(name)

            #If we find the face which is all_present_student in our database then mark the attendence
            if flag:
                collection.update_one({"name":name},{"$set":{current_date:'P'}})
                st.balloons()
                st.warning("Attendence marked")
            if flag==False:
                st.warning("You are not registerd.")

