from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient

from datetime import datetime, timedelta
import getLating

import jwt  # install PyJWT
import hashlib

from bson.objectid import ObjectId  # pymongo objectid

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.marumaru

SECRET_KEY = 'BAEMARUMARU'


# 메인페이지 불러오기
@app.route('/')
def main():
    return render_template('index.html')


# 게시물목록 페이지 불러오기
@app.route('/list')
def show_posts():
    return render_template('post_list.html')


# 게시물 리스트 불러오기
@app.route('/post_list', methods=['GET'])
def posts_list():
    articles = list(db.articles.find({}, {'_id': False}).sort([("number", -1)]))
    best = db.articles.find_one({}, {'_id': False}, sort=([("view", -1)]))
    return jsonify({'all_articles': articles, 'best': best})


# 이벤트 작성 페이지 불러오기
@app.route('/events')
def show_events():
    return render_template('event_upload.html')


# 이벤트 작성
@app.route('/events', methods=['POST'])
def event_upload():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_information = db.users.find_one({"username": payload["id"]})

    title_receive = request.form['title_give']
    address_receive = request.form['address_give']
    contents_receive = request.form['content_give']
    date_receive = request.form['date_give']
    present_date_receive = request.form['present_date_give']
    max_receive = request.form['max_give']

    file = request.files['file_give']

    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y년%m월%d일%H:%M:%S')

    filename = f'{mytime}-{extension[0]}'
    filename = "".join(i for i in filename if i not in "\/:*?<>|")
    filename = filename.strip()

    save_to = f'static/eventimg/{filename}.{extension[1]}'

    file.save(save_to)

    count = db.events.count()
    if count == 0:
        max_value = 1
    else:
        max_value = db.events.find_one(sort=[("number", -1)])['number'] + 1

    doc = {
        'number': max_value,
        'username': user_information["username"],
        'profile_name': user_information["profile_name"],
        'title': title_receive,
        'contents': contents_receive,
        'address': address_receive,
        'file': f'{filename}.{extension[1]}',
        'date': date_receive,
        'present_date': present_date_receive,
        'max': max_receive,
        'comment': list(),
        'like': list(),
        'join': list(),
        'like_count': 0,
        'view': 0
    }

    db.events.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})


# 이벤트 목록 페이지 불러오기
@app.route('/event/list')
def show_events_list():
    return render_template('event_list.html')


# 이벤트 리스트 불러오기
@app.route('/events/list', methods=['GET'])
def event_list():
    events = list(db.events.find({}, {'_id': False}))
    return jsonify({'result': 'success', 'all_events': events})


# 이벤트디테일 페이지 불러오기
@app.route('/event/detail/<id>', methods=['GET'])
def event_detail(id):
    db.events.update_one({'number': int(id)}, {'$inc': {'view': 1}})
    events = db.events.find_one({'number': int(id)}, {'_id': False})
    # event_join = events['join']
    # print(event_join)
    # username = db.users.distinct("username")
    # print(username)
    # join_users = [i for i in event_join if i in username]
    # join_user_list = []
    if events:
        # for join_user in join_users:
        #     user = db.users.find_one({'username': join_user})
        #     join_user_name = user['username']
        #     join_user_pic = user['profile_pic']
        #     doc = {
        #         'username': join_user_name,
        #         'profile_pic': join_user_pic
        #     }
        #     join_user_list.append(doc)
        # print(join_user_list)
        return render_template("event_detail.html", id=id, events_db=events)
    else:
        return render_template("error.html")


# 이벤트 삭제 api
@app.route('/event/detail', methods=['DELETE'])
def event_delete():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        username = user_info['username']

        id_receive = request.form['id_give']
        event = db.events.find_one({'number': int(id_receive)}, {'_id': False})
        post_name = event['username']

        if username == post_name:
            db.events.delete_one({'number': int(id_receive)})
            return jsonify({'result': 'success', 'msg': '이벤트가 삭제 되었습니다.'})
        else:
            return jsonify({'result': 'success', 'msg': '작성자만 삭제 가능합니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))


# 이벤트 디테일 수정 화면 GET
@app.route('/pre-eventDetail/<id>', methods=['GET'])
def event_detail_upload(id):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        username = user_info['username']
        events = db.events.find_one({'number': int(id)}, {'_id': False})
        post_name = events['username']
        if username == post_name:
            return render_template("event_detail_upload.html", events=events, id=id)
        else:
            return redirect(url_for("show_events_list"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("main"))


# 이벤트 디테일 수정 api
@app.route('/event/detail', methods=['PUT'])
def event_detail_post_upload():
    id_receive = request.form['id_give']
    title_receive = request.form['title_give']
    address_receive = request.form['address_give']
    contents_receive = request.form['contents_give']
    date_receive = request.form['date_give']
    max_receive = request.form['max_give']
    db.events.update_one({'number': int(id_receive)},
                         {'$set': {'title': title_receive, 'contents': contents_receive, 'address': address_receive,
                                   'date': date_receive, 'max': max_receive}})
    return jsonify({'result': 'success', 'msg': '게시물을 수정합니다!'})


# 이벤트 좋아요 기능
@app.route('/event/like', methods=['post'])
def update_event_like():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})
    my_username = user_info['username']
    event_id_receive = request.form["id_give"]

    past_like = db.events.find_one({'number': int(event_id_receive)}, {'_id': False})
    like_list = past_like['like']

    if my_username in like_list:
        db.events.update_one({'number': int(event_id_receive)}, {"$pull": {'like': my_username}})
    else:
        db.events.update_one({'number': int(event_id_receive)}, {"$push": {'like': my_username}})

    pre_like = db.events.find_one({'number': int(event_id_receive)}, {'_id': False})
    like_count = len(pre_like['like'])
    db.events.update_one({'number': int(event_id_receive)}, {'$set': {'like_count': like_count}})
    return jsonify({'result': 'success', 'msg': '완료!'})


# 이벤트 참가하기
@app.route('/event/join', methods=['post'])
def event_join():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})  # 참가하는 유저 정보
    my_username = user_info['username']

    event_id_receive = request.form["id_give"]
    past_join = db.events.find_one({'number': int(event_id_receive)}, {'_id': False})  # 참가할 이벤트

    join_dic = past_join['join']
    join_list = []
    for j in join_dic:
        join_list.append(j['username'])

    if my_username in join_list:
        print('hi')
        index = join_list.index(my_username)
        db.events.update_one({'number': int(event_id_receive)}, {"$pull": {'join': {'username': my_username}}})
        return jsonify({'result': 'success', 'msg': '참가 취소 완료!'})
    else:
        if len(join_list) < int(past_join['max']):
            db.events.update_one({'number': int(event_id_receive)}, {"$push": {'join': user_info}})
            return jsonify({'result': 'success', 'msg': '참가하기 완료!'})
        else:
            return jsonify({'result': 'success', 'msg': '참가 인원이 다 찼습니다.'})


# 이벤트 댓글 작성
@app.route('/event/comment', methods=['POST'])
def event_comment_upload():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})
    my_username = user_info['username']
    id_receive = request.form["id_give"]
    comment = request.form["comment_give"]
    doc = {"comment": comment, "user": my_username}
    db.events.update_one({'number': int(id_receive)}, {"$addToSet": {"comment": doc}})
    save_comment = db.articles.find_one({'number': int(id_receive)}, {'_id': False})
    return jsonify({'msg': '댓글 저장!', 'save_comment': save_comment})


# 메인페이지에 프로필 카드 보여주기
@app.route('/dog-profile/list', methods=['GET'])
def show_dog_profile():
    dog_profiles = list(db.profile.find({}, {'_id': False}))
    print(dog_profiles)
    return jsonify({'all_dog_profile': dog_profiles})


# 지도 맵핑
@app.route('/map', methods=['GET'])
def mapping():
    id = request.args["id"]
    address = db.articles.find_one({'number': int(id)}, {'_id': False})['address']
    address_coor = getLating.getLatLng(address)
    return render_template('locate_map.html', lat=address_coor[0], lon=address_coor[1])


# 디테일 페이지 불러오기
@app.route('/detail/<id>', methods=['GET'])
def detail(id):
    db.articles.update_one({'number': int(id)}, {'$inc': {'view': 1}})
    articles = db.articles.find_one({'number': int(id)}, {'_id': False})
    if articles:
        return render_template("detail.html", id=id, detail_db=articles)
    else:
        return render_template("error.html")


# 디테일 수정 화면 GET
@app.route('/per-detail/<id>/', methods=['GET'])
def detail_upload(id):
    post = db.articles.find_one({'number': int(id)}, {'_id': False})
    return render_template("detail_upload.html", post=post, id=id)


# 디테일 수정 api
@app.route('/detail', methods=['PUT'])
def detail_post_upload():
    id_receive = request.form["id_give"]
    title_receive = request.form["title_give"]
    contents_receive = request.form["contents_give"]

    db.articles.update_one({'number': int(id_receive)},
                           {'$set': {'title': title_receive, 'contents': contents_receive}})
    return jsonify({'result': 'success', 'msg': '게시물을 수정합니다!'})


# 디테일 삭제 api
@app.route('/detail', methods=['DELETE'])
def post_delete():
    id_receive = request.form["id_give"]
    db.articles.delete_one({'number': int(id_receive)})
    return jsonify({'result': 'success', 'msg': '게시글 삭제'})


# 게시물 작성페이지 불러오기
@app.route('/posts', methods=['GET'])
def show_posts_upload():
    return render_template('post_upload.html')


# 게시물 작성
@app.route('/posts', methods=['POST'])
def post_upload():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    username = payload['id']

    title_receive = request.form['title_give']
    address_receive = request.form['address_give']
    contents_receive = request.form['content_give']
    filename_receive = request.form['filename_give']

    file = request.files['file_give']

    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y년%m월%d일%H:%M:%S')

    filename = f'{mytime}-{extension[0]}'

    filename = "".join(i for i in filename if i not in "\/:*?<>|")

    filename = filename.strip()
    save_to = f'static/postimg/{filename}.{extension[1]}'
    file.save(save_to)

    count = db.articles.count()
    # 게시글 삭제시 중복 가능 ->   존재하는  number +1 로 바꿔야함
    if count == 0:
        max_value = 1
    else:
        max_value = db.articles.find_one(sort=[("number", -1)])['number'] + 1

    doc = {
        'title': title_receive,
        'contents': contents_receive,
        'address': address_receive,
        'number': max_value,
        'file': f'{filename}.{extension[1]}',
        'present_time': mytime,
        'comment': list(),
        'view': 0,
        'username': username
    }

    db.articles.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})


# 댓글 작성
@app.route('/comment', methods=['POST'])
def comment_upload():
    id_receive = request.form["id_give"]
    comment = request.form["comment_give"]

    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    my_name = db.users.find_one({"username": payload["id"]})

    doc = {"comment": comment, "user": my_name["username"]}
    db.articles.update_one({'number': int(id_receive)}, {"$addToSet": {"comment": doc}})
    save_comment = db.articles.find_one({'number': int(id_receive)}, {'_id': False})
    return jsonify({'msg': '댓글 저장!', 'save_comment': save_comment})


@app.route('/comment', methods=['DELETE'])
def comment_delete():
    idx = request.form["id_give"]

    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    my_name = db.users.find_one({"username": payload["id"]})
    print(my_name["username"])

    db.articles.update_one({"number": int(idx)}, {"$pull": {"comment": {"user": my_name["username"]}}})
    return {"result": "success"}


# 프로필 작성 페이지 불러오기
@app.route('/profile/create')
def show_profile_upload():
    return render_template('profile_upload.html')


# 프로필 작성
@app.route('/profile/create', methods=['POST'])
def profile_upload():
    name_receive = request.form["name_give"]
    age_receive = request.form["age_give"]
    gender_receive = request.form["gender_give"]
    comment_receive = request.form["comment_give"]

    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

    file = request.files['file_give']

    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y년%m월%d일%H:%M:%S')

    filename = f'{mytime}-{extension[0]}'
    filename = "".join(i for i in filename if i not in "\/:*?<>|")
    filename = filename.strip()

    save_to = f'static/profileimg/{filename}.{extension[1]}'

    file.save(save_to)

    count = db.profile.count()
    if count == 0:
        max_value = 1
    else:
        max_value = db.profile.find_one(sort=[("number", -1)])['number'] + 1

    doc = {
        'name': name_receive,
        'age': age_receive,
        'gender': gender_receive,
        'comment': comment_receive,
        'number': max_value,
        'file': f'{filename}.{extension[1]}',
        'username': payload['id'],
        'like': list(),
        'like_count': 0,
    }

    db.profile.insert_one(doc)

    # user 에 게시글 id 저장
    # babys = list(db.profile.find({"username" : payload['id']}))
    # baby=[]
    # for b in babys :
    #     baby.append(str(b['_id']))
    # # baby_id = str(baby['_id'])
    # db.users.update_one({"username":payload['id']}, {"$set":{'baby':baby}})
    #
    baby = db.profile.find_one({"username": payload['id']}, {'_id': False})

    return jsonify({'msg': '저장 완료!', 'baby': baby})


# 프로필 목록 불러오기
@app.route('/profiles')
def show_profile_list():
    return render_template('profile_list.html')


@app.route('/dogprofile/list', methods=['GET'])
def profile_list():
    profiles = list(db.profile.find({}, {'_id': False}))
    return jsonify({'all_profile': profiles})


# 프로필 상세 페이지 불러오기
@app.route('/profile/<id>', methods=['GET'])
def profile_detail(id):
    profiles = db.profile.find_one({'number': int(id)}, {'_id': False})
    return render_template("profile_detail.html", id=id, profile_db=profiles)


# 프로필 좋아요
@app.route('/dogprofile/like', methods=['POST'])
def profile_like():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_info = db.users.find_one({"username": payload["id"]})
    my_username = user_info['username']
    profile_id_receive = request.form["id_give"]
    past_like = db.profile.find_one({'number': int(profile_id_receive)}, {'_id': False})
    like_list = past_like['like']

    print(like_list)

    if my_username in like_list:
        db.profile.update_one({'number': int(profile_id_receive)}, {"$pull": {'like': my_username}})

    else:
        db.profile.update_one({'number': int(profile_id_receive)}, {"$push": {'like': my_username}})

    pre_like = db.profile.find_one({'number': int(profile_id_receive)}, {'_id': False})
    like_count = len(pre_like['like'])
    db.profile.update_one({'number': int(profile_id_receive)}, {'$set': {'like_count': like_count}})
    return jsonify({'result': 'success', 'msg': '좋아요!'})


# 프로필 카드 삭제 api
@app.route('/profile', methods=['DELETE'])
def profile_delete():
    id_receive = request.form["id_give"]
    db.profile.delete_one({'number': int(id_receive)})
    return jsonify({'result': 'success', 'msg': '프로필삭제'})


# 프로필 디테일 수정 화면 GET
@app.route('/dogdetail/<id>', methods=['GET'])
def show_dog_detail_upload(id):
    profiles = db.profile.find_one({'number': int(id)}, {'_id': False})
    return render_template("profile_detail_upload.html", profiles=profiles, id=id)


# 프로필 디테일 수정 api
@app.route('/profile', methods=['PUT'])
def dog_detail_upload():
    id_receive = request.form["id_give"]
    age_receive = request.form["age_give"]
    gender_receive = request.form["gender_give"]
    comment_receive = request.form["comment_give"]

    db.profile.update_one({'number': int(id_receive)},
                          {'$set': {'age': age_receive, 'gender': gender_receive, 'comment': comment_receive}})
    return jsonify({'result': 'success', 'msg': '저장되었습니다!'})


@app.route('/login', methods=['GET'])
def login():
    # 로그인 버튼 클릭시 - 쿠키에 값 있으면, 바로 로그인 추가

    return render_template('login.html')


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    # 중복확인
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "profile_pics/profile_placeholder.png",  # 프로필 사진 파일 이름(기본이미지)
        "profile_info": "",  # 프로필 한 마디
        "baby": list()  # 아가들 리스트
    }
    db.users.insert_one(doc)

    payload = {
        'id': username_receive,
        'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 4)  # 로그인 4시간 유지
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify({'result': 'success', 'token': token})


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 4)  # 로그인 4시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/user_info', methods=['GET'])
def user_info():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_information = db.users.find_one({"username": payload["id"]}, {'_id': False})
        return jsonify({'result': 'success', 'user_info': user_information})

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))


@app.route('/user_profile', methods=['GET', 'POST', 'DELETE'])
def user_profile():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_information = db.users.find_one({"username": payload["id"]}, {'_id': False})

    if request.method == 'POST':
        baby = list(db.profile.find({'username': payload['id']}))
        return render_template('user_profile_upload.html', user_info=user_information, baby=baby)

    elif request.method == 'GET':
        baby = list(db.profile.find({'username': payload['id']}))
        return render_template('user_profile.html', user_info=user_information, baby=baby)

    elif request.method == 'DELETE':

        db.profile.delete_many({'username': payload['id']})
        db.events.delete_many({'username': payload['id']})
        db.users.delete_one({'username': payload['id']})
        return jsonify({'result': 'success', 'msg': '행복하세요.'})


@app.route('/user_update', methods=['POST'])
def user_update():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    username = payload['id']

    # update
    name_receive = request.form['name_give']
    description_receive = request.form['description_give']
    file = request.files['file_give']
    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y%m%d_%H%M%S')

    filename = f'{username}-{extension[0]}{mytime}'

    filename = "".join(i for i in filename if i not in "\/:*?<>|")

    filename = filename.strip()
    save_to = f'static/profile_pics/{filename}.{extension[1]}'
    file.save(save_to)
    db.users.update_one({'username': username},
                        {'$set': {'profile_name': name_receive, 'profile_info': description_receive,
                                  'profile_pic': 'profile_pics/' + filename + '.' + extension[1]}})
    return jsonify({'result': 'success', 'msg': '프로필을 수정합니다!! > <'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
