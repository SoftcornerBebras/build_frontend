from rest_framework import generics, permissions
from rest_framework.response import Response
from usr.serializers import *
from usr.models import *
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from cmp.models import *
from ques.models import *
from ques.serializers import *
from cmp.serializers import * 
from com.models import *
from datetime import datetime,date
from datetime import time
from com.serializers import *
from BebrasBackend.constants import *
import requests 
from usr.password_encryption import encrypt,decrypt
import copy 
import six 
import time as t 
import os
from os import walk
import glob
# import pythoncom
# import win32com.client
# from win32com.client import Dispatch
from django.conf import settings
from django.http import HttpResponse
from django.http import FileResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
import json
from pptx import Presentation
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FileUploadParser,MultiPartParser
from PyPDF2 import PdfFileWriter, PdfFileReader
import shutil


class getCompetitionAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def getTotalTime(studentenrolled):
        studentresponse=studentResponse.objects.filter(studentEnrollmentID=studentenrolled)
        print(studentresponse)
        totalTime=0.0
        for res in studentresponse:
          totalTime=totalTime+res.time
        print(totalTime)
        totalTime=totalTime*60
        min, sec = divmod(totalTime, 60)
        hr, min = divmod(min, 60)
        totalTime = time(int(hr), int(min), int(sec))
        return totalTime
    def get(self, request):
      try:
        print(request.user.userID)
        cmpNames=[]
        studentenrolled=studentEnrollment.objects.filter(userID=request.user.userID)
        print(studentenrolled)
        if not studentenrolled.exists():
          return Response("Not registered  for any  Competitions",status=404)
        for data in studentenrolled:
          endDate=data.competitionAgeID.competitionID.endDate
          startDate=data.competitionAgeID.competitionID.startDate
          if endDate.date() >= datetime.now().date() and datetime.now().date()>=startDate.date():
            print(data.competitionAgeID.competitionID.competitionName,data.score)
            if data.score!=999:
              attempted=True
            else:
              attempted=False
            try:
              studentrespon=studentResponse.objects.filter(studentEnrollmentID=data)
              timetaken=getCompetitionAPI.getTotalTime(data)
              timeduration = datetime.combine(date.today(),data.competitionAgeID.competitionID.testDuration)-datetime.combine(date.today(),timetaken)
              timeduration= (datetime.min + timeduration).time()
                      
            except:
              timeduration=data.competitionAgeID.competitionID.testDuration
     
            cmpobj={"competitionname":data.competitionAgeID.competitionID.competitionName,"startDate":data.competitionAgeID.competitionID.startDate.date()
              ,"endDate":data.competitionAgeID.competitionID.endDate.date(),"testDuration":timeduration,"attempted":attempted}
            cmpNames.append(cmpobj)
        if len(cmpNames)==0:
          return Response("Sorry the competition you registered for has not started yet ",status=404)
        return  JsonResponse({"competitionnames":cmpNames}, safe=False)
      
      except Exception as e:
        return HttpResponse(e,status=404)

class getCmpQuestionAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def getTotalTime(studentenrolled):
        studentresponse=studentResponse.objects.filter(studentEnrollmentID=studentenrolled)
        print(studentresponse)
        totalTime=0.0
        for res in studentresponse:
          totalTime=totalTime+res.time
        print(totalTime)
        totalTime=totalTime*60
        min, sec = divmod(totalTime, 60)
        hr, min = divmod(min, 60)
        totalTime = time(int(hr), int(min), int(sec))
        return totalTime
    def post(self, request):
      try:
        testattempted=False
        response=[]
        print(request.data['competitionName'])
        compName=competition.objects.get(competitionName=request.data['competitionName'])
        print(compName)
        studentenrolled=studentEnrollment.objects.filter(userID=request.user.userID).values_list('competitionAgeID', flat=True)
        studentenrolled=list(studentenrolled)
        if len(studentenrolled)==0:
          return Response("Not registered for any competitions ",status=404)
        print(studentenrolled)
        try:
          cmpage = competitionAge.objects.get(competitionAgeID__in=studentenrolled,competitionID=compName.competitionID)
          print(cmpage)
        except:
          return Response("Either you are referring to a competition that student isn't enrolled for OR Same student has been  be registered for two different age groups  for the same competition",status=404)
        try: 
          studentEnrollmentlanguagecode=studentEnrollment.objects.get(competitionAgeID=cmpage.competitionAgeID,userID=request.user.userID)
        except:
          return Response("Same student has been  be registered twice for the same competition",status=404)
        
        cmpquestion=competitionQuestion.objects.filter(competitionAgeID=cmpage.competitionAgeID).values_list('questionID', flat=True)
        cmpquestion=list(cmpquestion)
        print((cmpquestion),studentEnrollmentlanguagecode.languageCodeID)
        questiontranslation=questionTranslation.objects.filter(questionID__in=cmpquestion,languageCodeID=studentEnrollmentlanguagecode.languageCodeID)
        print("total number of questions",len(questiontranslation))
        questiondata={}
        for quest in questiontranslation:
          questiondata={}
          questioncaption=quest.translation['caption']
          questionbackground=quest.translation['background']
          questiondata['question_caption']=questioncaption
          questiondata['question_background']=questionbackground
          questiondata['question_domain']=quest.questionID.domainCodeID.codeName
          questiondata['identifier']=quest.Identifier
          question_skills=""
          cs_skills=quest.questionID.cs_skills.split(',')
          print(cs_skills)
          for skill in cs_skills:
            skill=int(skill)
            codeskills=code.objects.get(codeID=skill)
            print(codeskills)
            if question_skills=="":
              question_skills=codeskills.codeName
            else:
              question_skills=question_skills+" , "+codeskills.codeName
          questiondata['question_cs_skills']=question_skills
          cmpquest=competitionQuestion.objects.get(questionID=quest.questionID , competitionAgeID=cmpage.competitionAgeID)
          print(cmpquest.questionID,cmpage.AgeGroupClassID.AgeGroupID)
          try:
             studentrespon=studentResponse.objects.get(studentEnrollmentID=studentEnrollmentlanguagecode,competitionQuestionID=cmpquest)
             questiondata['answered']=True
             testattempted=True
          except:
             questiondata['answered']=False
             print(" no backup strategy") 
      
          cmpMarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
          questiondata['question_marks']=cmpMarks.correctMarks
          correctoption=correctOption.objects.get(questionTranslationID=quest.questionTranslationID)
          if correctoption.ansText is None:
            if(quest.questionID.questionTypeCodeID.codeID==question_without_images):
              print("we came in question without images")
              questiondata['question_type']="question_without_images"
              optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
              optionlist=list(optionlist)
              optiontranslation = optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=studentEnrollmentlanguagecode.languageCodeID.codeID)
              print("no of options",len(optiontranslation))
           
              optiondata=[]
              for optiond in optiontranslation:
                  optiondata.append(optiond.translationO['option'])
              questiondata['options']=optiondata
              response.append(questiondata)
            elif(quest.questionID.questionTypeCodeID.codeID==question_with_images):
              print("we came in question with images")
              questiondata['question_type']="question_with_images"
              optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
              optionlist=list(optionlist)
              optiontranslation=optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=studentEnrollmentlanguagecode.languageCodeID.codeID)
              print("no of options",len(optiontranslation))
              image=Image.objects.filter(ImageTypeCodeID=imageOpt)
              imagop=[]
              for im in image:
                for op in optiontranslation:
                  if(im.ObjectID==op.optionID.optionID): #image me question id ki question translation id?
                    imagop.append(im.uploadedFile)
              if(imagop):
                print("option has imagees")  
                questiondata['images_of_option']=imagop
              optiondata=[]
              for optiond in optiontranslation:
                  optiondata.append(optiond.translationO['option'])
              questiondata['options']=optiondata
              response.append(questiondata)
          else:
            questiondata['question_type']="question_without_images_without_options"
            response.append(questiondata)
        print("done")
        if testattempted:
          print("test attempted ")
          timeduration=getCmpQuestionAPI.getTotalTime(studentEnrollmentlanguagecode)
          timeduration = datetime.combine(date.today(),studentEnrollmentlanguagecode.competitionAgeID.competitionID.testDuration)-datetime.combine(date.today(),timeduration)
          timeduration= (datetime.min + timeduration).time()
         
        else:
          timeduration=studentEnrollmentlanguagecode.competitionAgeID.competitionID.testDuration
        studentEnrollmentlanguagecode.timeTaken=datetime.now()
        studentEnrollmentlanguagecode.save()
        print("Time updated")
        return  JsonResponse({"questions":response,"studentEnrollmentID":studentEnrollmentlanguagecode.studentEnrollmentID,"timeduration":timeduration}, safe=False)
      except Exception as e:
        return HttpResponse(status=404)

class studentResponseAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    serializer_class = StudentResponseSerializer

    def post(self, request):
      try:
        print(request.data)
        ques=request.data['identifier']
        quesTranslation=questionTranslation.objects.get(Identifier=ques)
        print("got question ",quesTranslation)
        student_enrolled=studentEnrollment.objects.get(studentEnrollmentID=request.data['studentEnrollmentID'])
        print(student_enrolled)
        print(quesTranslation.questionID,student_enrolled.competitionAgeID)
        # assuming only competitionageid and question id will be a unique pair
        cmpques=competitionQuestion.objects.get(questionID=quesTranslation.questionID.questionID,competitionAgeID=student_enrolled.competitionAgeID)
        print(cmpques.competitionQuestionID)
        opt=request.data['option']
        opti=option.objects.filter(questionID=quesTranslation.questionID).values_list('optionID', flat=True)
        opti=list(opti)
        if len(opti)==0:
            if request.data['option']=="":
              request.data['ansText']=None
            else:
              request.data['ansText']=request.data['option']
            request.data['optionTranslationID']=None
        else:
            if opt=="":
              request.data['optionTranslationID']=None
              request.data['ansText']=None
            else:
              optiontext['option']=opt
              print(optiontext)
              opTranslation=optionTranslation.objects.get(translationO=optiontext,optionID__in=opti,languageCodeID=student_enrolled.languageCodeID) 
              print(opTranslation)
              request.data['optionTranslationID']=opTranslation.optionTranslationID
              request.data['ansText']=None
        request.data['competitionQuestionID']=cmpques.competitionQuestionID
        startTime=student_enrolled.timeTaken #START TIME refers to student enrollment time taken
        endTime=datetime.now().time()        #END TIME refers to the current time
        time_difference = datetime.combine(date.today(),endTime)-datetime.combine(date.today(),startTime)
        print(time_difference)
        time_diff=round(time_difference.seconds/60,4)
        print(time_diff)
        request.data['time']=time_diff
        del request.data['option']
        del request.data['identifier']
        print(request.data)   
        try:
          #student has already given response
          student_res=studentResponse.objects.get(competitionQuestionID=cmpques.competitionQuestionID,studentEnrollmentID=student_enrolled.studentEnrollmentID)
          print(student_res,time_diff)
          student_res.time=round(student_res.time,4)+time_diff
          print(request.data['optionTranslationID'],request.data['ansText'])
          if request.data['optionTranslationID']==None and request.data['ansText']==None:
            student_res.optionTranslationID=None
            student_res.ansText=None
          elif  request.data['optionTranslationID']!=None and request.data['ansText']==None:
            student_res.optionTranslationID=opTranslation
          else:
            student_res.ansText=request.data['ansText']
            print(student_res.ansText)
          student_res.save()
          print(" Student Response Updated")
        except studentResponse.DoesNotExist:
          #student is giving response for the first time
          serializer = StudentResponseSerializer(data=request.data)
          if serializer.is_valid():
            studentres = serializer.save() 
            print(" Student Response Saved")
          else:
            errors=''
            for i in serializer.errors : 
              errors=errors+ i +' '+ str(serializer.errors[i])
              errors="Error : "+errors
            return Response(errors,status=404)
        student_enrolled.timeTaken=datetime.now()
        student_enrolled.save()
        print("Time updated")  
        return Response("Success",status=200)
   
      except Exception as e:
        return HttpResponse(e,status=404)

class calcTotalScore(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    serializer_class = CorrectOptionSerializer

    def post(self, request):
      try:
        print(request.user.userID)
        studentenrolled=studentEnrollment.objects.get(studentEnrollmentID=request.data['studentEnrollmentID'])
        print(studentenrolled)
        studentenrolled.score=0
        studentenrolled.save()
        studentenrolled=studentEnrollment.objects.get(studentEnrollmentID=request.data['studentEnrollmentID'])
        cmpquest=competitionQuestion.objects.filter(competitionAgeID=studentenrolled.competitionAgeID)
        for data in cmpquest:
          questr=questionTranslation.objects.get(questionID=data.questionID,languageCodeID=studentenrolled.languageCodeID)
          correctOpt=correctOption.objects.get(questionTranslationID=questr.questionTranslationID)
          studentresponse=studentResponse.objects.get(studentEnrollmentID=studentenrolled,competitionQuestionID=data.competitionQuestionID)
          competition_Marks=competition_MarkScheme.objects.get(competitionAgeID=studentenrolled.competitionAgeID,questionLevelCodeID=studentresponse.competitionQuestionID.questionLevelCodeID)
          if correctOpt.optionTranslationID is not None:
            if studentresponse.optionTranslationID is not None:
              if correctOpt.optionTranslationID.optionTranslationID == studentresponse.optionTranslationID.optionTranslationID:
                print("correct")
                print(competition_Marks.correctMarks)
                studentenrolled.score=studentenrolled.score+competition_Marks.correctMarks
                studentenrolled.save()
                print("Score Saved")
              elif correctOpt.optionTranslationID.optionTranslationID != studentresponse.optionTranslationID.optionTranslationID:
                print("Incorrect")
                print(competition_Marks.incorrectMarks)
                studentenrolled.score=studentenrolled.score+competition_Marks.incorrectMarks
                studentenrolled.save()
                print(" Score Saved")

    
      
          elif correctOpt.optionTranslationID is  None and correctOpt.ansText is not None:
            if studentresponse.ansText is not None:
              if correctOpt.ansText == studentresponse.ansText:
                print("correct")
                print(competition_Marks.correctMarks)
                studentenrolled.score=studentenrolled.score+competition_Marks.correctMarks
                studentenrolled.save()
                print("Score Saved")
              elif correctOpt.ansText != studentresponse.ansText:
                print("Incorrect")
                print(competition_Marks.incorrectMarks)
                studentenrolled.score=studentenrolled.score+competition_Marks.incorrectMarks
                studentenrolled.save()
                print(" Score Saved")
        studentresponse=studentResponse.objects.filter(studentEnrollmentID=studentenrolled)
        totalTime=0.0
        for res in studentresponse:
          totalTime=totalTime+res.time
        print(totalTime)
        totalTime=totalTime*60
        min, sec = divmod(totalTime, 60)
        hr, min = divmod(min, 60)
        totalTime = time(int(hr), int(min), int(sec))
        studentenrolled.timeTaken=totalTime
        print("Time updated",totalTime)
        studentenrolled.save()
        return JsonResponse("success", safe=False)
      except Exception as e:
        return HttpResponse(e,status=404)     

class getCompetitionsNamesForResultAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def get(self, request):
      try:
        print("Received request from ",request.user.userID)
        cmpNames=[]
        studentenrolled=studentEnrollment.objects.filter(userID=request.user.userID)
        if not studentenrolled.exists():
          return Response("User hasn't registered for any of the competitions",status=404)
        print(studentenrolled)
        for data in studentenrolled:
           student_response=studentResponse.objects.filter(studentEnrollmentID=data.studentEnrollmentID)
           print(student_response)
           if student_response :
               print(student_response)
               cmpNames.append(data.competitionAgeID.competitionID.competitionName)
               print(cmpNames)
           else:
               print("Registered but not appeared for ",data.competitionAgeID.competitionID.competitionName)
        
        if len(cmpNames)==0:
          return Response("Sorry you haven't appeared for any competitions",status=404)
        return  JsonResponse({"competitionnames":cmpNames}, safe=False)
      
      except Exception as e:
        return HttpResponse(e,status=404)

class getCompetitionsNamesForAnalysisAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def get(self, request):
      try:
        print("Received request from ",request.user.userID)
        cmpNames=[]
        role_of_user=UserRole.objects.get(userID=request.user.userID)
        location_of_user=UserRoleLocation.objects.get(userRoleID=role_of_user)
        schoolname=school.objects.get(schoolID=location_of_user.locationObjectID)
        comp=competition.objects.all()
        for data in comp:
        
           if data.endDate.date() > schoolname.registered_On and data.competitionType.codeName==main_challenge :
               cmpNames.append(data.competitionName)
               print(cmpNames)
           else:
               print("Not appeared for ",data.competitionName)
        
        if len(cmpNames)==0:
          return Response("Sorry your school hasn't appeared for any competitions",status=404)
        return  JsonResponse({"competitionnames":cmpNames}, safe=False)
      
      except Exception as e:
        return HttpResponse(e,status=404)

class getCmpResultsAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def post(self, request):
      try:
        totalscore=0
        response=[]
        print("Request received from ",request.user.userID)
        compName=competition.objects.get(competitionName=request.data['competitionName'])
        print(compName)
        studentenrolled=studentEnrollment.objects.filter(userID=request.user.userID).values_list('competitionAgeID', flat=True)
        if not studentenrolled.exists():
          return Response("User hasn't registered for any of the competitions",status=404)
        studentenrolled=list(studentenrolled)
        print(studentenrolled)
        
        cmpage = competitionAge.objects.get(competitionAgeID__in=studentenrolled,competitionID=compName.competitionID)
        print(cmpage)
        try:
          studentEnrollmentlanguagecode=studentEnrollment.objects.get(competitionAgeID=cmpage.competitionAgeID,userID=request.user.userID)
        except:
          return Response("User has registered more than once for same competition",status=404)
        if studentEnrollmentlanguagecode.score==999:
          print("User hasn't completed the test")
          return Response("User hasn't completed the test",status=404)
        cmpquestion=competitionQuestion.objects.filter(competitionAgeID=cmpage.competitionAgeID).values_list('questionID', flat=True)
        cmpquestion=list(cmpquestion)
        questiontranslation=questionTranslation.objects.filter(questionID__in=cmpquestion,languageCodeID=studentEnrollmentlanguagecode.languageCodeID)
        print("total number of questions",len(questiontranslation))
        questiondata={}
        for quest in questiontranslation:
          questiondata={}
          questiondata['question_caption']=quest.translation['caption']
          questiondata['question_background']=quest.translation['background']
          questiondata['question_explanation']=quest.translation['explanation']      
          questiondata['question_domain']=quest.questionID.domainCodeID.codeName
          questiondata['identifier']=quest.Identifier
          question_skills=""
          cs_skills=quest.questionID.cs_skills.split(',')
          print(cs_skills)
          for skill in cs_skills:
            skill=int(skill)
            codeskills=code.objects.get(codeID=skill)
            print(codeskills)
            if question_skills=="":
              question_skills=codeskills.codeName
            else:
              question_skills=question_skills+" , "+codeskills.codeName
          questiondata['question_cs_skills']=question_skills
          correctoption=correctOption.objects.get(questionTranslationID=quest.questionTranslationID)
          cmpquest=competitionQuestion.objects.get(questionID=quest.questionID,competitionAgeID=cmpage.competitionAgeID)
          print(cmpquest.competitionQuestionID,studentEnrollmentlanguagecode.studentEnrollmentID)
          try:
            studentres=studentResponse.objects.get(competitionQuestionID=cmpquest.competitionQuestionID,studentEnrollmentID=studentEnrollmentlanguagecode.studentEnrollmentID)
            print(studentres)
            if correctoption.ansText is None:
              if(quest.questionID.questionTypeCodeID.codeID==question_without_images):
                print("we came in question without images")
                questiondata['question_type']="question_without_images"
                optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
                optionlist=list(optionlist)
                optiontranslation = optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=studentEnrollmentlanguagecode.languageCodeID.codeID)
                print("no of options",len(optiontranslation))
                optiondata=[]
                if studentres.optionTranslationID is None:
                  questiondata['selectedoption']="No option Selected"
                else:
                  print("Got user's selected option")
                  questiondata['selectedoption']=studentres.optionTranslationID.translationO['option']
                for optiond in optiontranslation:
                    optiondata.append(optiond.translationO['option'])
                questiondata['options']=optiondata
                questiondata['correctoption']=correctoption.optionTranslationID.translationO['option']
                cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
                questiondata['marks']=cmpmarks.correctMarks
                totalscore=totalscore+cmpmarks.correctMarks
                if(questiondata['selectedoption']==questiondata['correctoption']):
                  questiondata['Score']=cmpmarks.correctMarks
                elif questiondata['selectedoption']=="No option Selected":
                  questiondata['Score']=0
                else:
                  questiondata['Score']=cmpmarks.incorrectMarks
                
                response.append(questiondata)
              elif(quest.questionID.questionTypeCodeID.codeID==question_with_images):
                print("we came in question with images")
                questiondata['question_type']="question_with_images"
                optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
                optionlist=list(optionlist)
                optiontranslation=optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=studentEnrollmentlanguagecode.languageCodeID.codeID)
                print("no of options",len(optiontranslation))
                image=Image.objects.filter(ImageTypeCodeID=imageOpt)
                imagop=[]
                for im in image:
                  for op in optiontranslation:
                    if(im.ObjectID==op.optionID.optionID): #image me question id ki question translation id?
                      imagop.append(im.uploadedFile)
                if(imagop):
                  print("option has imagees")  
                  questiondata['images_of_option']=imagop
                if studentres.optionTranslationID is None:
                  questiondata['selectedoption']="No option Selected"
                else:
                  print("Got user's selected option")
                  questiondata['selectedoption']=studentres.optionTranslationID.translationO['option']
                optiondata=[]
                for optiond in optiontranslation:
                    optiondata.append(optiond.translationO['option'])
                questiondata['options']=optiondata
                questiondata['correctoption']=correctoption.optionTranslationID.translationO['option']
                cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
                print(cmpmarks)
                questiondata['marks']=cmpmarks.correctMarks
                totalscore=totalscore+cmpmarks.correctMarks
                if(questiondata['selectedoption']==questiondata['correctoption']):
                  questiondata['Score']=cmpmarks.correctMarks
                elif questiondata['selectedoption']=="No option Selected":
                  questiondata['Score']=0
                else:
                  questiondata['Score']=cmpmarks.incorrectMarks
                print(questiondata)
                response.append(questiondata)
              
            else:
              questiondata['question_type']="question_without_images_without_options"
              questiondata['correctoption']=correctoption.ansText
              questiondata['selectedoption']=studentres.ansText
              cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
              questiondata['marks']=cmpmarks.correctMarks
              totalscore=totalscore+cmpmarks.correctMarks
              if correctoption.ansText == studentres.ansText:
                questiondata['Score']=cmpmarks.correctMarks
              elif  studentres.ansText == "" or studentres.ansText==None:
                questiondata['Score']=0
              else :
                questiondata['Score']=cmpmarks.incorrectMarks

              response.append(questiondata)
            
          except studentResponse.DoesNotExist:
            if correctoption.ansText is None:
              if(quest.questionID.questionTypeCodeID.codeID==question_without_images):
                print("we came in question without images")
                questiondata['question_type']="question_without_images"
                optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
                optionlist=list(optionlist)
                optiontranslation = optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=studentEnrollmentlanguagecode.languageCodeID.codeID)
                print("no of options",len(optiontranslation))
                optiondata=[]
                questiondata['selectedoption']="No option Selected"
                for optiond in optiontranslation:
                    optiondata.append(optiond.translationO['option'])
                questiondata['options']=optiondata
                questiondata['correctoption']=correctoption.optionTranslationID.translationO['option']
                cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
                questiondata['marks']=cmpmarks.correctMarks
                totalscore=totalscore+cmpmarks.correctMarks
                questiondata['Score']=0
                response.append(questiondata)
              elif(quest.questionID.questionTypeCodeID.codeID==question_with_images):
                print("we came in question with images")
                questiondata['question_type']="question_with_images"
                optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
                optionlist=list(optionlist)
                optiontranslation=optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=studentEnrollmentlanguagecode.languageCodeID.codeID)
                print("no of options",len(optiontranslation))
                image=Image.objects.filter(ImageTypeCodeID=imageOpt)
                imagop=[]
                for im in image:
                  for op in optiontranslation:
                    if(im.ObjectID==op.optionID.optionID): #image me question id ki question translation id?
                      imagop.append(im.uploadedFile)
                if(imagop):
                  print("option has imagees")  
                  questiondata['images_of_option']=imagop
                
                questiondata['selectedoption']="No option Selected"
                
                optiondata=[]
                for optiond in optiontranslation:
                    optiondata.append(optiond.translationO['option'])
                questiondata['options']=optiondata
                questiondata['correctoption']=correctoption.optionTranslationID.translationO['option']
                cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
                print(cmpmarks)
                questiondata['marks']=cmpmarks.correctMarks
                totalscore=totalscore+cmpmarks.correctMarks
                questiondata['Score']=0
                print(questiondata)
                response.append(questiondata)
              
            else:
              questiondata['question_type']="question_without_images_without_options"
              questiondata['correctoption']=correctoption.ansText
              questiondata['selectedoption']="No option Selected"
              cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
              questiondata['marks']=cmpmarks.correctMarks
              totalscore=totalscore+cmpmarks.correctMarks
              questiondata['Score']=0
              print(questiondata)
              response.append(questiondata)
            
          except:
            return Response("One or more responses for the same question",status=404)

        print("done")
        return  JsonResponse({"questions":response,"studentID":request.user.loginID,"studentName":request.user.username,"TotalScore":studentEnrollmentlanguagecode.score,"totalMarks":totalscore}, safe=False)
      except Exception as e:
        return HttpResponse(e,status=404)

class LanguageAPI(APIView):

    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def post(self, request):
      try:
        print(request.data)
        lang=[]
        comp=competition.objects.get(competitionName=request.data['competitionName'])
        compAge=competitionAge.objects.filter(competitionID=comp)
        print(list(compAge))
        for data in compAge:
          print(data.AgeGroupClassID.ClassID.classID)
          if data.AgeGroupClassID.ClassID.classID==request.data['class_id']:
            langarr=data.AgeGroupClassID.AgeGroupID.AgeGroupName.split('-')
            print(langarr[1])
            lang.append(langarr[1])
         
        if len(lang)==0:
          return Response("No languages to show for the selected competition",status=404)    
        return JsonResponse({"languages":lang}, safe=False)
      except Exception as e:
        return HttpResponse(e,status=404)

class practiceChallengeNames(APIView):

    permission_classes = [
      permissions.AllowAny,
    ]
    def get(self, request):
      try:
        comp=competition.objects.filter(competitionType=practice_challenge)
        challenges=[]
        challengesnames=[]
        print(len(comp))
        for data in comp:
          startDate=data.startDate.date()
          today=datetime.now().date()
          endDate=data.endDate.date()
         
          if today > startDate and today < endDate:
            challenges.append(data.competitionID)
        cmpage=competitionAge.objects.filter(competitionID__in=challenges)
        print(len(cmpage))
        for data in cmpage:
          challengesnames.append(data.AgeGroupClassID.AgeGroupID.AgeGroupName)
        challengesnames = set(challengesnames)
        print(challengesnames)
        challengesnames = list(challengesnames)
        if len(challengesnames)==0:
          return Response("No Practice Challenge to show ",status=404)    
        return JsonResponse({"PracticeChallenges":challengesnames}, safe=False)
      except Exception as e:
        return HttpResponse(e,status=404)

class PracChallengeQuestionAPI(generics.GenericAPIView):
    permission_classes = [
      permissions.AllowAny,
    ]
    def post(self, request):
      try:
        response=[]
        print(request.data['AgeGroupName'])
        lang=request.data['AgeGroupName'].split('-')
        language=code.objects.get(codeName=lang[1])
        print(language)
        compage=competitionAge.objects.all()
        cmps=[]
        print(len(compage))
        for comps in compage:
          today=datetime.now().date()
          endDate=comps.competitionID.endDate.date()
          if comps.AgeGroupClassID.AgeGroupID.AgeGroupName== request.data['AgeGroupName'] and comps.competitionID.competitionType.codeID==practice_challenge and today<endDate:
            cmps.append(comps.competitionID.competitionName)
        cmps=set(cmps)
        cmps=list(cmps)
        if(len(cmps)>1):
          return Response("Something went wrong",status=404)
        compName=competition.objects.filter(competitionName=cmps[0])
        print(compName[0])
        newcmp=None
        cmpage = competitionAge.objects.filter(competitionID=compName[0].competitionID).values_list('competitionAgeID', flat=True)
        print((cmpage))
        if len(cmpage)==2:
          
          cmpage1=competitionAge.objects.get(competitionAgeID=cmpage[0])
          print(cmpage1.AgeGroupClassID)
          cmpage2=competitionAge.objects.get(competitionAgeID=cmpage[1])
          print(cmpage2.AgeGroupClassID)
          if cmpage1.AgeGroupClassID.AgeGroupID.AgeGroupName==cmpage2.AgeGroupClassID.AgeGroupID.AgeGroupName:
            newcmp=cmpage1
            print(newcmp)
        else:
          return Response("Something went wrong",status=404)
        cmpage=newcmp
        
        cmpquestion=competitionQuestion.objects.filter(competitionAgeID=cmpage.competitionAgeID).values_list('questionID', flat=True)
        cmpquestion=list(cmpquestion)
        print(len(cmpquestion))
        questiontranslation=questionTranslation.objects.filter(questionID__in=cmpquestion,languageCodeID=language)
        print("total number of questions",len(questiontranslation))
        questiondata={}
        for quest in questiontranslation:
          questiondata={}
          questiondata['question_caption']=quest.translation['caption']
          questiondata['question_background']=quest.translation['background']
          questiondata['question_explanation']=quest.translation['explanation']
          questiondata['question_domain']=quest.questionID.domainCodeID.codeName
          questiondata['identifier']=quest.Identifier
          question_skills=""
          cs_skills=quest.questionID.cs_skills.split(',')
          print(cs_skills)
          for skill in cs_skills:
            skill=int(skill)
            codeskills=code.objects.get(codeID=skill)
            print(codeskills)
            if question_skills=="":
              question_skills=codeskills.codeName
            else:
              question_skills=question_skills+" , "+codeskills.codeName
          questiondata['question_cs_skills']=question_skills
          correctoption=correctOption.objects.get(questionTranslationID=quest.questionTranslationID)
          cmpquest=competitionQuestion.objects.get(questionID=quest.questionID,competitionAgeID=cmpage.competitionAgeID)
        
          if correctoption.ansText is None:
            if(quest.questionID.questionTypeCodeID.codeID==question_without_images):
              print("we came in question without images")
              questiondata['question_type']="question_without_images"
              optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
              optionlist=list(optionlist)
              optiontranslation = optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=language.codeID)
              print("no of options",len(optiontranslation))
              optiondata=[]
         
              for optiond in optiontranslation:
                  optiondata.append(optiond.translationO['option'])
              questiondata['options']=optiondata
              questiondata['correctoption']=correctoption.optionTranslationID.translationO['option']
              print(quest.questionID,cmpage.AgeGroupClassID.AgeGroupID)
    
              cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
              questiondata['Correct_marks']=cmpmarks.correctMarks
              questiondata['Incorrect_marks']=cmpmarks.incorrectMarks
              response.append(questiondata)
            elif(quest.questionID.questionTypeCodeID.codeID==question_with_images):
              print("we came in question with images")
              questiondata['question_type']="question_with_images"
              optionlist=option.objects.filter(questionID=quest.questionID).values_list('optionID', flat=True)
              optionlist=list(optionlist)
              optiontranslation=optionTranslation.objects.filter(optionID__in=optionlist,languageCodeID=language.codeID)
              print("no of options",len(optiontranslation))
              image=Image.objects.filter(ImageTypeCodeID=imageOpt)
              imagop=[]
              for im in image:
                for op in optiontranslation:
                  if(im.ObjectID==op.optionID.optionID): #image me question id ki question translation id?
                    imagop.append(im.uploadedFile)
              if(imagop):
                print("option has imagees")  
                questiondata['images_of_option']=imagop
            
              optiondata=[]
              for optiond in optiontranslation:
                  optiondata.append(optiond.translationO['option'])
              questiondata['options']=optiondata
              questiondata['correctoption']=correctoption.optionTranslationID.translationO['option']
              cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
              print(cmpmarks)
              questiondata['Correct_marks']=cmpmarks.correctMarks
              questiondata['Incorrect_marks']=cmpmarks.incorrectMarks
             
          
              print(questiondata)
              response.append(questiondata)
             
          else:
            questiondata['question_type']="question_without_images_without_options"
            questiondata['correctoption']=correctoption.ansText
            cmpmarks=competition_MarkScheme.objects.get(competitionAgeID=cmpage.competitionAgeID,questionLevelCodeID=cmpquest.questionLevelCodeID)
            print(cmpmarks)
            questiondata['Correct_marks']=cmpmarks.correctMarks
            questiondata['Incorrect_marks']=cmpmarks.incorrectMarks
            response.append(questiondata)
        print("done")
        return  JsonResponse({"questions":response}, safe=False)
      except Exception as e:
        return HttpResponse(e,status=404)

class GetAgeGroupToppers(APIView):
    def get(self,request,**kwargs):
        competitions=competition.objects.all()
        for comp in competitions:
          if comp.endDate.year==datetime.now().year and comp.competitionType.codeName == main_challenge:
            cmpcurrent=comp
        if cmpcurrent.endDate.date() > datetime.now().date():
          print("previous year")
          for comp in competitions:
            if comp.endDate.year==(datetime.now().year-1) and comp.competitionType.codeName == main_challenge:
              cmpcurrent=comp
        stud=[]
        ageGroupDict=[]
        responsedata=[]
        ageGroupList = []
        
        cmpage=competitionAge.objects.filter(competitionID=cmpcurrent)
        for compage in cmpage:
          ageGroupList.append(compage.AgeGroupClassID.AgeGroupID.AgeGroupName)
          try:
            studentenrolled=studentEnrollment.objects.filter(~Q(score = 999),competitionAgeID=compage).order_by('-score','timeTaken')
            if len(studentenrolled)!=0:
              stud.append(studentenrolled[0].studentEnrollmentID)
          except:
            return Response(status=400)
        ageGroupList=set(ageGroupList)
        print(ageGroupList)
        timecurrent=time(int(1), int(1), int(30))
        for data in ageGroupList:
          studenttop={'AgeGroup':data,'score':0,'time':timecurrent}
          ageGroupDict.append(studenttop)
        print(ageGroupDict)
        for d in ageGroupDict:
          topperdata={}
          for student in stud:
            studentenroll=studentEnrollment.objects.get(studentEnrollmentID=student)
            resdata={}
            resdata['studentName']=studentenroll.userID.username
            resdata['schoolName']=studentenroll.schoolClassID.schoolID.schoolName
            resdata['gender']=studentenroll.userID.gender.codeName
            resdata['time']=studentenroll.timeTaken
            resdata['rank']=1
            resdata['score']=studentenroll.score
            resdata['AgeGroup']=studentenroll.competitionAgeID.AgeGroupClassID.AgeGroupID.AgeGroupName
          
            if d['AgeGroup']==studentenroll.competitionAgeID.AgeGroupClassID.AgeGroupID.AgeGroupName and d['score']<studentenroll.score:
                d['score']=studentenroll.score
                topperdata=resdata
                d['time']=studentenroll.timeTaken
            elif d['AgeGroup']==studentenroll.competitionAgeID.AgeGroupClassID.AgeGroupID.AgeGroupName and d['score']==studentenroll.score and d['time']>studentenroll.timeTaken:
                d['time']=studentenroll.timeTaken
                topperdata=resdata
            elif d['AgeGroup']==studentenroll.competitionAgeID.AgeGroupClassID.AgeGroupID.AgeGroupName and d['score']==studentenroll.score and d['time']==studentenroll.timeTaken:
                topperdata=resdata
          responsedata.append(topperdata)
        return Response({"toppers":responsedata,"competitionName":cmpcurrent.competitionName},status=200)

class GetSchoolToppers(APIView):
    def getTotalscore(competitionAgeid):
      totalscore=0
      compques=competitionQuestion.objects.filter(competitionAgeID=competitionAgeid)
      for ques in compques:
          competition_MarkS=competition_MarkScheme.objects.get(competitionAgeID=competitionAgeid,questionLevelCodeID=ques.questionLevelCodeID)
            
          totalscore=totalscore+competition_MarkS.correctMarks
      return totalscore
    def post(self,request,**kwargs):
        token=request.META.get('HTTP_AUTHORIZATION')
        c = CustomizePPT()
        t= GetLatestTemplate()
        g=GetStudentsAgeGroupWise()
        d=g.post(request,json=request.data, format='json',headers={'Authorization': token})
        template=t.get(request,type='School_Toppers')
        print('Latest',template.data)
        print((d.data))
        if len(d.data) == 0:
          return Response("no students from this class were enrolled for the competition",status=404)
        data=[]
    
        for i in range(0, len(d.data)):
            compage=competitionAge.objects.get(competitionAgeID=d.data[i]['competitionAgeID'])
            userdata=User.objects.get(userID=d.data[i]['userID'])
            schoolclassdata=schoolClass.objects.get(schoolClassID=d.data[i]['schoolClassID'])
            data.append({'year':compage.competitionID.startDate.year,
                         'Name':userdata.username,
                         'loginID':userdata.loginID,
                         'group':compage.AgeGroupClassID.AgeGroupID.AgeGroupName,
                         'score':str(d.data[i]['score']),
                         'total':GetParticipationCertificates.getTotalscore(d.data[i]['competitionAgeID']),
                         'time': d.data[i]['timeTaken'],
                         'class':str(schoolclassdata.classNumber)})
       

     
        school=schoolclassdata.schoolID.schoolName+', '+schoolclassdata.schoolID.addressID.city
        type='schoolToppers'
        c.ppt(os.path.join(settings.MEDIA_ROOT) + '/ppt//'+template.data, data, school,type,duplicate=False)
        path_response=  school + '-Toppers-' + data[0][ 'group'] + '-' +str(data[0]['year'])
        return Response({"path":path_response},status=200)

class GetSchoolClassStudents(APIView):
    def post(self,request,**kwargs):
        print(request.user.userID)
        cmpname=request.data['cmpName']
        usrrole=UserRole.objects.get(userID=request.user.userID)
        print(usrrole)
        usrroleLocation=UserRoleLocation.objects.get(userRoleID=usrrole.userRoleID)
        print(usrroleLocation.locationObjectID)
        school_name = school.objects.get(schoolID=usrroleLocation.locationObjectID)
        comp= competition.objects.get(competitionName=cmpname)
        schclass=schoolClass.objects.get(schoolID=school_name.schoolID,classNumber=request.data['class_id'])
        print(schclass)
        cmpAge= competitionAge.objects.filter(competitionID=comp.competitionID )
        print(cmpAge)
        for data in cmpAge:
          print(data.AgeGroupClassID.ClassID.classID,request.data['class_id'])
          if data.AgeGroupClassID.ClassID.classID==request.data['class_id']:
            compage=data
            print(compage)
            break
        lists = studentEnrollment.objects.filter(~Q(score = 999),schoolClassID=schclass,competitionAgeID=compage.competitionAgeID)
        print(len(lists))
        if len(lists)==0:
          return Response("no students from this class were enrolled for the competition",status=404)
        serializer= studentEnrollmentViewSerializer(lists,many=True)
        return Response(serializer.data)

class GetParticipationCertificatesforStudentPortal(APIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def post(self, request,**kwargs ):
        print(request.user.created_by,request.data['competitionName'])
        current_user=User.objects.get(loginID=request.user.created_by)
        c = CustomizePPT()
        usrrole=UserRole.objects.get(userID=current_user.userID)
        print(usrrole)
        usrroleLocation=UserRoleLocation.objects.get(userRoleID=usrrole.userRoleID)
        print(usrroleLocation.locationObjectID)
        school_name = school.objects.get(schoolID=usrroleLocation.locationObjectID)
        studentsenroll=studentEnrollment.objects.filter(userID=request.user.userID)
        for students in studentsenroll:
          if students.competitionAgeID.competitionID.competitionName==request.data['competitionName']:
            data_user=students
            break
        t=GetLatestTemplate()
        print("Here in certificates for Student Portal",data_user)
        data=[]
        print(data_user.competitionAgeID)
        totalscore=GetSchoolToppers.getTotalscore(data_user.competitionAgeID)
        template=t.get(request,type='Participation')
        print('Latest',template.data)
      
        data.append({'year':data_user.competitionAgeID.competitionID.startDate.year,
                         'Name':request.user.username,
                         'loginID':request.user.loginID,
                         'group':data_user.competitionAgeID.AgeGroupClassID.AgeGroupID.AgeGroupName,
                         'score':str(data_user.score),
                         'total':totalscore,
                         'class':str(data_user.competitionAgeID.AgeGroupClassID.ClassID.classID)})
           
        print(data)
       
        schooldata=school_name.schoolName+', '+school_name.addressID.city
        type='participation'
        path_response=schooldata+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])
        c.ppt(os.path.join(settings.MEDIA_ROOT) + '/ppt//'+template.data, data, school,type,duplicate=False)
        return Response({"path":path_response},status=200)

class GetParticipationCertificatesforSelectedStudents(APIView):
    permission_classes = [
      permissions.IsAuthenticated,
    ]
    def post(self, request,**kwargs ):
        print(request.user.userID)
        c = CustomizePPT()
        usrrole=UserRole.objects.get(userID=request.user.userID)
        print(usrrole)
        usrroleLocation=UserRoleLocation.objects.get(userRoleID=usrrole.userRoleID)
        print(usrroleLocation.locationObjectID)
        school_name = school.objects.get(schoolID=usrroleLocation.locationObjectID)
       
        t=GetLatestTemplate()
        data_user=request.data['users']
        print("Here in cert",data_user)
        data=[]
     
       
        template=t.get(request,type='Participation')
        print('Latest',template.data)
        for i in data_user:
            print(i['loginID'])
            comp= competition.objects.get(competitionName=i['competitionName'])
            data.append({'year':comp.startDate.year,
                         'Name':i['username'],
                         'loginID':i['loginID'],
                         'group':i['ageGroup'],
                         'score':str(i['score']),
                         'total':i['Totalscore'],
                         'class':str(i['class'])})
           
        print(data)
       
        schooldata=school_name.schoolName+', '+school_name.addressID.city
        type='participation'
        path_response=schooldata+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])

        c.ppt(os.path.join(settings.MEDIA_ROOT) + '/ppt//'+template.data, data, schooldata,type,duplicate=True)
        return Response({"path":path_response},status=200)

class GetParticipationCertificates(APIView):

    def getTotalscore(competitionAgeid):
      print(competitionAgeid)
      totalscore=0
      compques=competitionQuestion.objects.filter(competitionAgeID=competitionAgeid)
      for ques in compques:
          competition_MarkS=competition_MarkScheme.objects.get(competitionAgeID=competitionAgeid,questionLevelCodeID=ques.questionLevelCodeID)   
          totalscore=totalscore+competition_MarkS.correctMarks
      return totalscore
    def post(self, request,**kwargs ):
        token=request.META.get('HTTP_AUTHORIZATION')
        c = CustomizePPT()
        g=GetSchoolClassStudents()
        t=GetLatestTemplate()
        d=g.post(request,json=request.data, format='json',headers={'Authorization': token})
        print("Here in cert",d.data)
        if d.data == "no students from this class were enrolled for the competition":
          return Response("no students from this class were enrolled for the competition",status=404)
        data=[]
        template=t.get(request,type='Participation')
        print('Latest',template.data)
        for i in range(0,len(d.data)):
            compage=competitionAge.objects.get(competitionAgeID=d.data[i]['competitionAgeID'])
            userdata=User.objects.get(userID=d.data[i]['userID'])
            schoolclassdata=schoolClass.objects.get(schoolClassID=d.data[i]['schoolClassID'])
            data.append({'year':compage.competitionID.startDate.year,
                         'Name':userdata.username,
                          'loginID':userdata.loginID,
                         'group':compage.AgeGroupClassID.AgeGroupID.AgeGroupName,
                         'score':str(d.data[i]['score']),
                         'total':GetParticipationCertificates.getTotalscore(d.data[i]['competitionAgeID']),
                         'class':str(schoolclassdata.classNumber)})
         
        print((schoolclassdata.schoolID.schoolName))
        school=schoolclassdata.schoolID.schoolName+', '+schoolclassdata.schoolID.addressID.city
        type='participation'
        path_response=school+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])

        c.ppt(os.path.join(settings.MEDIA_ROOT) + '/ppt//'+template.data, data, school,type,duplicate=True)
        return Response({"path":path_response},status=200)

class GetStudentsAgeGroupWise(APIView):
    def post(self,request,**kwargs):
        print(request.user.userID,request.data['class_id'])
        cmpname=request.data['cmpName']
        comp= competition.objects.get(competitionName=cmpname)
        usrrole=UserRole.objects.get(userID=request.user.userID)
        usrroleLocation=UserRoleLocation.objects.get(userRoleID=usrrole.userRoleID)
        school_name = school.objects.get(schoolID=usrroleLocation.locationObjectID)
        schclass=schoolClass.objects.get(schoolID=school_name.schoolID,classNumber=request.data['class_id'])
        cmpAge= competitionAge.objects.filter(competitionID=comp.competitionID )
        for data in cmpAge:
          print(data.AgeGroupClassID.ClassID.classID,request.data['class_id'])
          if data.AgeGroupClassID.ClassID.classID==request.data['class_id']:
            compage=data
            print(compage)
            break
        agegrps=AgeGroup.objects.filter(AgeGroupName=compage.AgeGroupClassID.AgeGroupID.AgeGroupName)
        agegroupid=0
        for i in range(0,len(agegrps)):
            if str(comp.startDate.year) in str(agegrps[i].created_on):
                agegroupid=agegrps[i].AgeGroupID
                break
        agegrpclasses=AgeGroupClass.objects.filter(AgeGroupID=agegroupid)
        agegroupclasses=[]
        for i in range(0,len(agegrpclasses)):
            agegroupclasses.append(agegrpclasses[i].AgeGroupClassID)
        cmpage=competitionAge.objects.filter(AgeGroupClassID__in= agegroupclasses)
        print(cmpage)
        cmpages=[]
        for i in range(0, len(cmpage)):
            cmpages.append(cmpage[i].competitionAgeID)

        schoolclasses = schoolClass.objects.filter(schoolID=school_name.schoolID)
        schclasses = []
        for i in range(0, len(schoolclasses)):
            schclasses.append(schoolclasses[i].schoolClassID)
        lists = studentEnrollment.objects.filter(~Q(score = 999),competitionAgeID__in =cmpages,schoolClassID__in=schclasses).order_by('-score','timeTaken')
        serializers=studentEnrollmentViewSerializer(lists,many=True)
        return Response(serializers.data)

@parser_classes((MultiPartParser,))
class CustomizePPT(APIView):
    def ppt(self,f,data,school,type,duplicate):
        prs = Presentation(f)
        NamesOfParticipants = []
        NOP = []
        text_runs = []
        def duplicate_slide(pres, index):
            template = pres.slides[index]
            try:
                blank_slide_layout = pres.slide_layouts[6]
            except:
                blank_slide_layout = pres.slide_layouts[len(pres.slide_layouts) - 1]
            copied_slide = pres.slides.add_slide(blank_slide_layout)
            for shp in template.shapes:
                el = shp.element
                newel = copy.deepcopy(el)
                copied_slide.shapes._spTree.insert_element_before(newel, 'p:extLst')
            for _, value in six.iteritems(template.part.rels):
                if "notesSlide" not in value.reltype:
                    copied_slide.part.rels.add_relationship(value.reltype,
                                                            value._target,
                                                            value.rId)
            return copied_slide
        if duplicate==True:
            for i in range(0,len(data)-1):
                duplicate_slide(prs, 0)
        i = -1
        print("Count",len(prs.slides))
        for slide in prs.slides:
            if i < (len(data) - 1):
                i = i + 1
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            for run in paragraph.runs:
                                if (shape.text.find('Name')) != -1:
                                    cur_text = run.text
                                    nameofPDF=data[i]['Name']+'-'+data[i]['loginID']+'-'+str(data[i]['year'])
                                    NamesOfParticipants.append(nameofPDF)
                                    new_text = cur_text.replace(str('Name'), str(data[i]['Name']))
                                    run.text = new_text
                                if (shape.text.find('year')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str('year'), str(data[i]['year']))
                                    run.text = new_text
                                if (shape.text.find('class')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str('class'), str(data[i]['class']))
                                    run.text = new_text
                                if (shape.text.find('group')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str('group'), str(data[i]['group']))
                                    run.text = new_text
                                if (shape.text.find('score')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str('score'), str(data[i]['score']))
                                    run.text = new_text
                                if (shape.text.find('total')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str('total'), str(data[i]['total']))
                                    run.text = new_text
                                if (shape.text.find('[')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str('['), str(''))
                                    run.text = new_text
                                if (shape.text.find(']')) != -1:
                                    cur_text = run.text
                                    new_text = cur_text.replace(str(']'), str(''))
                                    run.text = new_text
            else:
                rId = prs.slides._sldIdLst[-1].rId
                prs.part.drop_rel(rId)
                del prs.slides._sldIdLst[-1]
        if(type=='participation'):
          NOP = NamesOfParticipants[::2]
        elif(type=='schoolToppers'):
          NOP = NamesOfParticipants
        path=''
        ldir = os.path.join(settings.MEDIA_ROOT) + '/output//'
        if(len(ldir)!=0):
          shutil.rmtree(ldir)
          os.makedirs(os.path.join(settings.MEDIA_ROOT) +'/output//')
        if(type=='participation'):
            print('/output//'+school+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])+'pptx')
            path=os.path.join(settings.MEDIA_ROOT) + '/output//'+school+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])+'.pptx'
        elif(type=='schoolToppers'):
            path=os.path.join(settings.MEDIA_ROOT) + '/output//' + school + '-Toppers-' + data[0][ 'group'] + '-' +str(data[0]['year'])+'.pptx'
        elif (type == 'nationalToppers'):
            path = os.path.join(settings.MEDIA_ROOT) + '/output//' +  'National Toppers-' + data[0]['group'] + '-' + data[0]['year'] + '.pptx'
        prs.save(path)
        # pythoncom.CoInitialize()
        def zipdir(self,source):
            print("Entered zipdir")
            pdfName=''
            if(type=='participation'):
                pdfName=school+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])
            elif(type=='schoolToppers'):
                pdfName=school + '-Toppers-' + data[0][ 'group'] + '-' +str(data[0]['year'])
            basedir = pdfName
            baseName = os.path.join(settings.MEDIA_ROOT) + '/Zipfolder/BebrasCertificate'
            shutil.make_archive(base_dir=basedir,root_dir=source,format='zip',base_name=baseName)
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT) + '/Zipfolder//'+pdfName)
            print("Done!")
        def splitPDF(self,path1):
            pdfName=''
            if(type=='participation'):
                pdfName=school+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])
                CertiFolder = os.path.join(settings.MEDIA_ROOT)+'/Zipfolder//'+pdfName
                os.makedirs(CertiFolder)
            elif(type=='schoolToppers'):
                pdfName=school + '-Toppers-' + data[0][ 'group'] + '-' +str(data[0]['year'])
                CertiFolder = os.path.join(settings.MEDIA_ROOT)+'/Zipfolder//'+pdfName
                os.makedirs(CertiFolder)
            pdfFileObj = open(path1, "rb")
            inputpdf = PdfFileReader(pdfFileObj)
            i=0
            print(inputpdf.numPages)
            if(inputpdf.numPages==1):
                output = PdfFileWriter()
                output.addPage(inputpdf.getPage(i))
                outputFileName = os.path.join((settings.MEDIA_ROOT)+'/Zipfolder//'+pdfName,NOP[0]+".pdf" )
                with open(outputFileName, "wb") as outputStream:
                  output.write(outputStream)
            else:
                for i in range(inputpdf.numPages):
                    output = PdfFileWriter()
                    output.addPage(inputpdf.getPage(i))
                    outputFileName = os.path.join((settings.MEDIA_ROOT)+'/Zipfolder//'+pdfName,NOP[i]+".pdf")
                    with open(outputFileName, "wb") as outputStream:
                      output.write(outputStream)
            pdfFileObj.close()
        # def convert(files, formatType=32):
        #     powerpoint = win32com.client.Dispatch("Powerpoint.Application")
        #     powerpoint.Visible = 1
        #     print("ppt",powerpoint)
        #     for filename in files:
        #         newname = os.path.splitext(filename)[0] + ".pdf"
        #         print(filename)
        #         deck = powerpoint.Presentations.Open(filename,WithWindow=False)
        #         deck.SaveAs(newname, formatType)
        #         deck.Close()
        #     powerpoint.Quit()
        files = glob.glob(path)  # <--- ONLY CHANGE
        # convert(files)
        for filename in files:
                # command="libreoffice --headless --invisible --convert-to pdf '" + filename +"'"
                command = "unoconv -f pdf '" + filename+"'"
                os.system(command)
                os.remove(path)
        ldir =(os.path.join(settings.MEDIA_ROOT) + '/Zipfolder//')
        if(len(ldir)!=0):
          shutil.rmtree(ldir)
          os.makedirs(os.path.join(settings.MEDIA_ROOT) +'/Zipfolder//')
        path1=''
        if(type=='participation'):
            path1=os.path.join(settings.MEDIA_ROOT) + '/output//'+school+'-Class-'+data[0]['class']+'-'+data[0]['group']+'-'+str(data[0]['year'])+'.pdf'
        elif(type=='schoolToppers'):
            path1=os.path.join(settings.MEDIA_ROOT) + '/output//' + school + '-Toppers-' + data[0][ 'group'] + '-' +str(data[0]['year'])+'.pdf'
        splitPDF(self,path1)
        source= os.path.join(settings.MEDIA_ROOT) + '/Zipfolder//'
        zipdir(self,source)
        os.remove(path)

class deleteFiles(APIView):
    c = CustomizePPT()
    ppt = c.ppt
    def post(self,request,**kwargs):
      
        type=request.data['CertificateType']
        if(type=='participation'):
            os.remove(os.path.join(settings.MEDIA_ROOT) + '/output//'+request.data["path"]+ '.pdf')
        if(type=='schoolToppers'):
            os.remove(os.path.join(settings.MEDIA_ROOT) +  '/output//'+request.data["path"]+ '.pdf')
       
        os.remove(os.path.join(settings.MEDIA_ROOT) + '/ZipFolder/BebrasCertificate'+'.zip')
        return Response(status=200)

class GetLatestTemplate(APIView):               #Get Latest Template API
    authentication_classes = (TokenAuthentication, )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self,request,**kwargs):
        type=kwargs['type']
        f = []
        for (dirpath, dirnames, filenames) in walk(os.path.join(settings.MEDIA_ROOT) + ("/ppt/")):
            for file in filenames:
                if (file.find(type) != -1):
                    f.append(file)
            break
        datetimes=[]
        for i in range(0,len(f)):
            arr=f[i].split('_')
            datetimes.append(arr[len(arr)-2]+'_'+arr[len(arr)-1].split('.')[0])
            sortedArray = sorted(
            datetimes,
            key=lambda x: datetime.strptime(x, '%Y-%m-%d_%H-%M-%S'), reverse=True
            )
        for i in range(0,len(f)):
            if str(sortedArray[0]) in f[i]:
                name=f[i]
                break
        return Response(name)