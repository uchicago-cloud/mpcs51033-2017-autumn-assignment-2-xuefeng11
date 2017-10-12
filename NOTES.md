Xuefeng Liu
Assignement 2

-Completed and tested all the functionalities in the requirement.
-Fixed all error and warnings
-Added addition web page to smooth the process.

Instructions:
1. need register a new users by
  https://project-2-photo-timeline.appspot.com/register/

2. need authenticate
by putting the user name and password
copy the token_id on the page, attach it to end of every request
https://project-2-photo-timeline.appspot.com/user/authenticate/?username=xuefeng111&password=123456

curl -X GET https://project-2-photo-timeline.appspot.com/user/authenticate/?username=xuefeng111&password=123456

3. check json output
 https://project-2-photo-timeline.appspot.com/user/xuefeng111/json/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

 curl -X GET https://project-2-photo-timeline.appspot.com/user/xuefeng111/json/?id_token=f0a7abc4-729f-466e-b674-54217addf97a


4. check html web output
 https://project-2-photo-timeline.appspot.com/user/xuefeng111/web/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

 curl -X GET https://project-2-photo-timeline.appspot.com/user/xuefeng111/web/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

5. show image: copy the image key from json out. for example:"image/ahpzfnByb2plY3QtMi1waG90by10aW1lbGluZXISCxIFUGhvdG8YgICAgKvzhwoM/?id_token=f0a7abc4-729f-466e-b674-54217addf97a"
https://project-2-photo-timeline.appspot.com/image/ahpzfnByb2plY3QtMi1waG90by10aW1lbGluZXISCxIFUGhvdG8YgICAgKvzhwoM/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

curl -X GET https://project-2-photo-timeline.appspot.com/image/ahpzfnByb2plY3QtMi1waG90by10aW1lbGluZXISCxIFUGhvdG8YgICAgN6QgQkM/?id_token=f0a7abc4-729f-466e-b674-54217addf97a
 
6. delete image: by insert "/delete/"before "?token_id="
https://project-2-photo-timeline.appspot.com/image/ahpzfnByb2plY3QtMi1waG90by10aW1lbGluZXISCxIFUGhvdG8YgICAgKvzhwoM/delete/?id_token=f0a7abc4-729f-466e-b674-54217addf97a
curl -X GET https://project-2-photo-timeline.appspot.com/image/ahpzfnByb2plY3QtMi1waG90by10aW1lbGluZXISCxIFUGhvdG8YgICAgN6QgQkM/delete/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

7. using the logging
https://project-2-photo-timeline.appspot.com/logging/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

curl -X GET https://project-2-photo-timeline.appspot.com/logging/?id_token=f0a7abc4-729f-466e-b674-54217addf97a

-testing on google cloud
gcloud app deploy app.yaml index.yaml --project project-2-photo-timeline
gcloud app browse --project project-2-photo-timeline

-testing locally
dev_appserver.py --clear_datastore=yes app.yaml
dev_appserver.py ./

-curl testing
change project-2-photo-timeline.appspot.com to localhost:8080 to test locally