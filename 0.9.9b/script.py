# coding: utf-8
import webiopi
import RPi.GPIO as GPIO
import configparser
import json
import mysql.connector as mc
import os
import random
import signal
import string
import time
from datetime import datetime

VERSION = '0.9.9b'
# GPIO pin using BCM numbering
ENABLE     = 2
BET        = 3
START      = 4
STOP1      = 5
STOP2      = 6
STOP3      = 7
AUTO       = 8
NERAI_1    = 9
NERAI_2    = 10
CHANCE     = 11
#SETUP      = 12
#SET_1      = 13
#SET_2      = 14
#SET_3      = 15
#CALL       = 16
CREDIT_DEC = 20
CREDIT_INC = 21
STATUS_AP  = 22
#MEDAL_DEC  = 23
#MEDAL_INC  = 24
STATUS_RB  = 25
STATUS_BB  = 26
STATUS_CT  = 27
# error code
ERR_RASPI   = 801
ERR_HISTORY = 802
ERR_POINT   = 803
ERR_USER    = 804
ERR_DUP     = 805 #0429
ERR_CONNECTION = 808 # 816
# output
inifile = '../python/rp.ini'
logpath = '../log/'
logfile = 'webiopi.log'
start   = 'data/in.json'
output  = 'data/rp.json'
stop    = 'data/out.json'
# database
RP_ID = 0
DNS = {}
# Environment value
evBR_MUTEX = 0
evNERAI = 1
evCHANCE = 1 #0603
evNAME = ''
evPORT_VIDEO = 0
evHOME = ''
evMOMO = ''
evTIME_OUT = 0
evOPEN_TIME = ''
evCLOSE_TIME = ''
evAG_MAX = 0
evRT = 0
evRM = 0
evQS = 0 # 816
# -------------
sess    = ''
jsonkey = ''
userid  = 0
credit  = 0
point = 0
st_ap = 0
st_ct = 0
st_rb = 0
st_bb = 0
#medal = 0
game  = 0
auto_play = 0
auto_count = 0 # 200310
nerai_mode = 0
rb_sig_timer = 0
bb_sig_timer = 0
term_flg = 0 # 200315
error_code = 0
# -------------
gmCount = 0
bbCount = 0
rbCount = 0
bwCount = 0
# -------------
chkdt = 0 # 816
start_flg = 0 # 0329
# -------------
# サーバー側データベース更新用クラス
class ServerDB:
    global DNS
    global jsonkey
    global RP_ID
    global userid
    global sess
    global start_flg
    point = 0
    credit = 0
    enable = 0 #enablx
    def setPoint(self, point):
        self.point = point
    def getPoint(self):
        return self.point
    def setCredit(self, credit):
        self.credit = credit
    def getCredit(self):
        return self.credit
    def setEbable(self, enable): # enablex
        self.credit = credit
    def getEbable(self): # enable
        return self.enable
    def initDb(self):
        if start_flg == 1 and self.point > 2:
            conn = mc.connect(**DNS)
            cur = conn.cursor(prepared=True)
            try:
                stmt = "insert into user_history (user_id,`point`,remain_point,operation,op_user_id,op_raspi_id,op_date,session_id,json_id) values (?,?,?,1,null,?,now(),?,?)"
                cur.execute(stmt, (userid, 0, self.point, RP_ID, sess, jsonkey))
                conn.commit()
                stmt = "update raspi set json_id=? where id=?"
                cur.execute(stmt, (jsonkey, RP_ID))
                conn.commit()
                stmt = "update raspi_history set json_id=? where raspi_id=? and user_id=? and session_id=?"
                cur.execute(stmt, (jsonkey, RP_ID, userid, sess,))
                conn.commit()
            except mc.Error as e:
                printLog('- ERROR - mode=' + str(mode) + ' ' + e.msg)
            finally:
                cur.close
                conn.close
    def updateDb(self, point):
        if start_flg == 1 and self.point > 2:
            conn = mc.connect(**DNS)
            cur = conn.cursor(prepared=True)
            try:
                stmt = "update user_history set `point`=?, remain_point=?, op_date=now() where user_id=? and op_raspi_id=? and session_id=? and json_id=?"
                cur.execute(stmt, (point, self.point, userid, RP_ID, sess, jsonkey))
                if cur.rowcount == 0: # 20220110 -------
                    printLog('DB-error has occurred. -- update user_history --')
                    Game_Finalize(0, -1) # term
                    setActive(0)
                else:
                    conn.commit()
                    stmt = "update users set `point`=? where id=?"
                    cur.execute(stmt, (self.point, userid))
                    if cur.rowcount == 0:
                        printLog('DB-error has occurred. -- update users --')
                        Game_Finalize(0, -1) # term
                        setActive(0)
                    else:
                        conn.commit()
            except mc.Error as e:
                printLog('- ERROR - mode=' + str(mode) + ' ' + e.msg)
            finally:
                cur.close
                conn.close
    def termDb(self, point):
        if start_flg == 1:
            conn = mc.connect(**DNS)
            cur = conn.cursor(prepared=True)
            try:
                stmt = "update user_history set `point`=?, remain_point=?, op_date=now() where user_id=? and op_raspi_id=? and session_id=? and json_id=?"
#                cur.execute(stmt, (point, self.point, userid, RP_ID, sess, jsonkey))
#                conn.commit()
                stmt = "update users set `point`=? where id=?"
#                cur.execute(stmt, (self.point, userid))
#                conn.commit()
            except mc.Error as e:
                printLog('- ERROR - mode=' + str(mode) + ' ' + e.msg)
            finally:
                cur.close
                conn.close
    def setStatus(self, status): # maintenance
        try:
            stmt = "update raspi set `status`=? where id=?"
            cur.execute(stmt, (status, RP_ID))
            printLog('- start maintenance -')
        except mc.Error as e:
            printLog('- ERROR - maintenance ' + e.msg)
        finally:
            cur.close
            conn.close

RPDB = ServerDB()

class Timer:
    now = datetime.now()
    def __init__(self, tm):
        self.tm = tm
    def setTimer(self, id):
        self.id = id
        self.now = datetime.now()
    def clearTimer(self, id):
        self.id = id
    def checkTimer(self, id):
        self.id = id
        sec = (datetime.now() - self.now).seconds
#        printLog("start=" + str(self.now) + "  span=" + str(sec))

timer = Timer(10000)

def setup():
    global RP_ID
    global DNS
    global timer

    config = configparser.ConfigParser()
    config.read(inifile)
    RP_ID = config.get('general', 'id')
    DNS = {'user': config.get('database', 'user'), 'password': config.get('database', 'pass'), 'host': config.get('database', 'host'), 'database': config.get('database', 'name')}
    GPIO.setmode(GPIO.BCM)
    for i in range(16):
        GPIO.setup(i + 2, GPIO.OUT)
    for i in range(8):
        GPIO.setup(i + 20, GPIO.IN)
        GPIO.setup(i + 20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for i in range(16):
        GPIO.output(i + 2, 0)
    GPIO.add_event_detect(CREDIT_DEC, GPIO.RISING, bouncetime=5)
    GPIO.add_event_callback(CREDIT_DEC, event_callback_credit_dec)
    GPIO.add_event_detect(CREDIT_INC, GPIO.RISING, bouncetime=5)
    GPIO.add_event_callback(CREDIT_INC, event_callback_credit_inc)

    GPIO.add_event_detect(STATUS_AP, GPIO.BOTH, bouncetime=5)
    GPIO.add_event_callback(STATUS_AP, event_callback_status_ap)
    GPIO.add_event_detect(STATUS_RB, GPIO.BOTH, bouncetime=5)
    GPIO.add_event_callback(STATUS_RB, event_callback_status_rb)
    GPIO.add_event_detect(STATUS_BB, GPIO.BOTH, bouncetime=5)
    GPIO.add_event_callback(STATUS_BB, event_callback_status_bb)
    GPIO.add_event_detect(STATUS_CT, GPIO.BOTH, bouncetime=5)
    GPIO.add_event_callback(STATUS_CT, event_callback_status_ct)

# 095
#    GPIO.add_event_detect(MEDAL_DEC, GPIO.RISING, bouncetime=5)
#    GPIO.add_event_callback(MEDAL_DEC, event_callback_medal_dec)
#    GPIO.add_event_detect(MEDAL_INC, GPIO.RISING, bouncetime=5)
#    GPIO.add_event_callback(MEDAL_INC, event_callback_medal_inc)
    # ----------------------------------------------------------
    time.sleep(180)# 3分位待たないとエラー(101 Network is unreachable)になる
    setResetTime()
    printLog("- INFO - Startup - id=" + RP_ID + " name=" + evNAME + " script_version=" + VERSION + " time_out=" + str(evTIME_OUT) + " reset_time=" + str(evRT) + " reset_minute=" + str(evRM))

def loop():
    global chkdt # 816
    global timer
    now = datetime.now()
#    if int(evRT) + int(evRM) != 46:
    if ((now.hour == evRT) and (now.minute == evRM) and (now.second == 0)):
        clearCount() # reset
    if chkdt != 0:
        if (abs(now - chkdt)).seconds > evQS:
            Game_Finalize(1, -1) # term
            setActive(0)
            printLog('td=' + td + ' now=' + now + ' chkdt=' + chkdt)
            chkdt = 0
    timer.checkTimer(12)
    webiopi.sleep(0.1)

def event_callback_credit_dec(gpio_pin):
    global credit
    global point
    time.sleep(0.05) # 200402
#    if GPIO.input(CREDIT_INC) == GPIO.LOW: # 200402
    if credit != 0: # 200305
        credit = int(credit) - 1
        point = int(point) - 1

def event_callback_credit_inc(gpio_pin):
    global credit
    global point
    time.sleep(0.05) # 200402
#    if GPIO.input(CREDIT_INC) == GPIO.LOW: # 200402
    credit = int(credit) + 1
    point = int(point) + 1

# 095
#def event_callback_medal_dec(gpio_pin):
#    global medal
#    time.sleep(0.01) # 191205
#    if GPIO.input(MEDAL_DEC) == GPIO.LOW: # 191205
#        medal = int(medal) - 1

#def event_callback_medal_inc(gpio_pin):
#    global medal
#    time.sleep(0.01) # 191205
#    if GPIO.input(MEDAL_INC) == GPIO.LOW: # 191205
#        medal = int(medal) + 1

def event_callback_status_ap(gpio_pin):
    global st_ap
    if GPIO.input(STATUS_AP) == GPIO.LOW:
        time.sleep(0.01) # 191205
        if GPIO.input(STATUS_AP) == GPIO.LOW: # 191205
            st_ap = 1
    else:
        st_ap = 0

def event_callback_status_rb(gpio_pin):
    global st_rb
    global rbCount
    global bwCount
    global rb_sig_timer
    if GPIO.input(STATUS_RB) == GPIO.LOW:
        time.sleep(0.01)
        rb_sig_timer
        if GPIO.input(STATUS_RB) == GPIO.LOW:
            time.sleep(0.1)
            if GPIO.input(STATUS_RB) == GPIO.LOW:
                if (st_bb == 0 and st_rb == 0):
                    st_rb = 1
                    rbCount = int(rbCount) + 1
                    countUp(bwCount, 2) # bb:2
                    bwCount = 0
    else:
        rb_sig_timer = 0

def event_callback_status_bb(gpio_pin):
    global st_bb
    global bbCount
    global bwCount
    global bb_sig_timer
    if GPIO.input(STATUS_BB) == GPIO.LOW:
        time.sleep(0.01)
        bb_sig_timer = 0
        if GPIO.input(STATUS_BB) == GPIO.LOW:
            time.sleep(0.1)
            if GPIO.input(STATUS_BB) == GPIO.LOW:
                if st_bb == 0:
                    st_bb = 1
                    bbCount = int(bbCount) + 1
                    countUp(bwCount, 1) # bb:1
                    bwCount = 0
    else:
        bb_sig_timer = 0

def event_callback_status_ct(gpio_pin):
    global st_ct
    global game
    global gmCount
    global bwCount # 191206
    global auto_count # 0310
    if GPIO.input(STATUS_CT) == GPIO.LOW:
        time.sleep(0.01) # 191205
        if GPIO.input(STATUS_CT) == GPIO.LOW: # 191205
            time.sleep(0.01)
            if GPIO.input(STATUS_CT) == GPIO.LOW:
                st_ct = 0
                if (st_bb == 0 and st_rb == 0):
                    game = int(game) + 1
                    gmCount = int(gmCount) + 1
                    bwCount = int (bwCount) + 1 # 191206
                    if (auto_play == 1): # 0310
                        auto_count = int(auto_count) + 1 # 0310

#    global st_ct
#    global game
#    global gmCount
#    global bwCount # 191206
#    if GPIO.input(STATUS_CT) == GPIO.LOW:
#        time.sleep(0.01) # 191205
#        if GPIO.input(STATUS_CT) == GPIO.LOW: # 191205
#            st_ct = 1
#    else:
#        st_ct = 0
#        if (st_bb == 0 and st_rb == 0):
#            game = int(game) + 1
#            gmCount = int(gmCount) + 1
#            bwCount = int (bwCount) + 1 # 191206

# ################################
def getSessionID():
    return str.upper(''.join([random.choice(string.ascii_letters + string.digits) for i in range(32)]))

# ################################
def printLog(msg):
    with open(logpath + logfile, 'a') as f:
        print('%s %s' % (datetime.now().strftime("%Y/%m/%d %H:%M:%S"), msg), file=f)

# ################################
def rotateLog():
    path1 = logpath + logfile
    if (os.path.exists(path1)):
        file1 = open(path1, 'r', encoding='utf-8')
        f1 = file1.readline()
        file1.close()
        if (len(f1) > 20):
            path2 = logpath + 'webiopi-' + str(f1[:19]).replace('/', '').replace(' ', '').replace(':', '') + '.log'
            os.rename(path1, path2)

# ################################
def setResetTime():
    global evBR_MUTEX
    global evNERAI
    global evCHANCE # 0603
    global evNAME
    global evPORT_VIDEO
    global evHOME
    global evMOMO
    global evTIME_OUT
    global evOPEN_TIME
    global evCLOSE_TIME
    global evAG_MAX
    global evRT
    global evRM
    global evQS
    try:
        conn = mc.connect(**DNS)
        cur = conn.cursor(prepared=True)
        cur.execute("select `value` from setting where `key`='DOMAIN'")
        record = cur.fetchone()
        evHOME = record[0].decode('utf-8')
        cur.execute("select `value` from setting where `key`='RP_DOMAIN'")
        record = cur.fetchone()
        evMOMO = record[0].decode('utf-8')
        cur.execute("select `value` from setting where `key`='TIME_OUT_PLAY'")
        record = cur.fetchone()
        evTIME_OUT = record[0].decode('utf-8')
        cur.execute("select `value` from setting where `key`='OPEN'")
        record = cur.fetchone()
        evOPEN_TIME = record[0].decode('utf-8')
        cur.execute("select `value` from setting where `key`='CLOSE'")
        record = cur.fetchone()
        evCLOSE_TIME = record[0].decode('utf-8')
        cur.execute("select `value` from setting where `key`='AG_MAX'")
        record = cur.fetchone()
        evAG_MAX = record[0].decode('utf-8')
        stmt = "select concat(s.name,'(',r.slot_num,')'),r.port_video,cast(date_format(r.reset_time, '%k') as signed),cast(date_format(r.reset_time, '%i') as signed),qrysec from raspi r left join slot s on r.slot_id=s.id where r.id=?"
        cur.execute(stmt, (RP_ID,))
        record = cur.fetchone()
        evNAME = record[0].decode('utf-8')
        evPORT_VIDEO = record[1]
        evRT = record[2]
        evRM = record[3]
        evQS = record[4] # 816
        cpuinfo = getCpuinfo()
        stmt = "update raspi set revision=?,serial=?,model=?,script_version=?,boot_date=now() where id=?"
        cur.execute(stmt, (cpuinfo["Revision"], cpuinfo["Serial"], cpuinfo["Model"], VERSION, RP_ID))
    except mc.Error as e:
        printLog('- ERROR - MySQL - ' + e.msg)
    finally:
        cur.close
        conn.close

# ################################
def clearCount():
    global gmCount
    global bbCount
    global rbCount
#    global bwCount
    global credit
    global point
    global evRT
    global evRM
    try:
        conn = mc.connect(**DNS)
        cur = conn.cursor(prepared=True)
        stmt = "select CAST(DATE_FORMAT(reset_time, '%k') AS SIGNED),CAST(DATE_FORMAT(reset_time, '%i') AS SIGNED) from raspi where `id`=?"
        cur.execute(stmt, (RP_ID,))
        record = cur.fetchone()
        if record[0] == int(evRT) and record[1] == int(evRM):
            stmt = "select * from raspi_status where raspi_id=? and status_date=CAST(now() AS DATE)"
            cur.execute(stmt, (RP_ID,))
            record = cur.fetchone()
            if (record == None):
                stmt = "insert into raspi_status value (?,?,?,?,?,?,now())"
                cur.execute(stmt, (RP_ID,datetime.now().date(),int(gmCount),int(bbCount),int(rbCount),int(bwCount)))
                conn.commit()
                gmCount = 0
                bbCount = 0
                rbCount = 0
#                bwCount = 0
#                point = 0
#                credit = 0
                printLog('- INFO - All counter was cleared.')
                stmt = "update raspi set st_game=0,st_bb=0,st_rb=0,st_bw=0 where `id`=?"
                cur.execute(stmt, (RP_ID,))
                conn.commit()
                rotateLog()
                printLog("- INFO - Restart - id=" + RP_ID + " name=" + evNAME + " script_version=" + VERSION + " time_out=" + str(evTIME_OUT) + " reset_time=" + str(evRT) + " reset_minute=" + str(evRM))
        else:
            evRT = record[0]
            evRM = record[1]
            printLog('- ERROR - All ounter couldn\'t cleared - new RT:' + str(record[0]) + ' RM:' + str(record[1]))
    except mc.Error as e:
        printLog('- ERROR - MySQL - ' + e.msg)
    finally:
        cur.close
        conn.close

# ################################
def getCpuinfo():
    cpuinfo = {}
    os.system('cat /proc/cpuinfo > ../python/cpuinfo')
    file_name = "../python/cpuinfo"
    try:
        file = open(file_name)
        lines = file.readlines()
        for line in lines:
            if ('Revision' in line):
                cpuinfo["Revision"] = (line[line.find(':') + 2:]).replace('\n' , '')
            if ('Serial' in line):
                cpuinfo["Serial"] = (line[line.find(':') + 2:]).replace('\n' , '')
            if ('Model' in line):
                cpuinfo["Model"] = (line[line.find(':') + 2:]).replace('\n' , '')
    except Exception as e:
        print(e)
    finally:
        file.close()
    return cpuinfo

# ################################
def countUp(count, btype):
    try:
        conn = mc.connect(**DNS)
        cur = conn.cursor(prepared=True)
        stmt = "insert into raspi_counter values (?,?,?,?,now())"
        cur.execute(stmt, (RP_ID, userid, count, btype))
        conn.commit()
    except mc.Error as e:
        printLog('- ERROR - MySQL - ' + e.msg)
    finally:
        cur.close
        conn.close

# ################################
def destroy():
    GPIO.remove_event_detect(CREDIT_DEC)
    GPIO.remove_event_detect(CREDIT_INC)
# 095
#    GPIO.remove_event_detect(MEDAL_DEC)
#    GPIO.remove_event_detect(MEDAL_INC)
    GPIO.remove_event_detect(STATUS_AP)
    GPIO.remove_event_detect(STATUS_RB)
    GPIO.remove_event_detect(STATUS_BB)
    GPIO.remove_event_detect(STATUS_CT)
    GPIO.cleanup()

# ################################
# WebIOPi macros
# ################################
# maintenance
@webiopi.macro
def setMaintenance(e):
	global RPDB
	RPDB.setStatus(4)

@webiopi.macro
def setActive(e):
    global st_rb
    global rb_sig_timer
    global st_bb
    global bb_sig_timer
    global game
    global start_flg #092
    global point #091
    global credit #091
    if (int(e) > 0):
        GPIO.output(ENABLE, GPIO.HIGH)
    else:
        GPIO.output(ENABLE, GPIO.LOW)
        GPIO.output(AUTO, GPIO.LOW) # 0313
        start_flg = 0 #092
        credit = 0 #091
        point = 0 #091

    if GPIO.input(STATUS_BB) == GPIO.HIGH:
        if st_bb != 0:
            bb_sig_timer = bb_sig_timer + 1
            if bb_sig_timer == 2:
                st_bb = 0
                bb_sig_timer = 0
                game = 0
        else:
            bb_sig_timer = 0
    else:
        bb_sig_timer = 0

    if GPIO.input(STATUS_RB) == GPIO.HIGH:
        if st_rb != 0:
            rb_sig_timer = rb_sig_timer + 1
            if rb_sig_timer == 2:
                st_rb = 0
                rb_sig_timer = 0
                if st_bb == 0:
                    game = 0
        else:
            rb_sig_timer = 0
    else:
        rb_sig_timer = 0

# --------------------------------
# オート
# --------------------------------
@webiopi.macro
def btnAuto():
    global auto_play
    global auto_count # 0310
    auto_play = 0 if auto_play == 1 else 1
    if auto_play == 1:
        GPIO.output(AUTO, GPIO.HIGH)
        auto_count = 0 # 0310
    else:
        GPIO.output(AUTO, GPIO.LOW)

# --------------------------------
# CHANCE
# --------------------------------
@webiopi.macro
def btnChance():
    GPIO.output(CHANCE, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(CHANCE, GPIO.LOW)

# --------------------------------
# 狙い1
# --------------------------------
@webiopi.macro
def btnNerai1():
    global nerai_mode
    nerai_mode = 0 if nerai_mode == 1 else 1
    if nerai_mode == 1:
        GPIO.output(NERAI_1, GPIO.HIGH)
        GPIO.output(NERAI_2, GPIO.LOW)
    else:
        GPIO.output(NERAI_1, GPIO.LOW)
        GPIO.output(NERAI_2, GPIO.LOW)

# --------------------------------
# 狙い2
# --------------------------------
# 095
#@webiopi.macro
#def btnNerai2():
#    global nerai_mode
#    nerai_mode = 0 if nerai_mode == 2 else 2
#    if nerai_mode == 2:
#        GPIO.output(NERAI_1, GPIO.LOW)
#        GPIO.output(NERAI_2, GPIO.HIGH)
#    else:
#        GPIO.output(NERAI_1, GPIO.LOW)
#        GPIO.output(NERAI_2, GPIO.LOW)

# --------------------------------
# 狙い3
# --------------------------------
# 095
#@webiopi.macro
#def btnNerai3():
#    global nerai_mode
#    nerai_mode = 0 if nerai_mode == 3 else 3
#    if nerai_mode == 3:
#        GPIO.output(NERAI_1, GPIO.HIGH)
#        GPIO.output(NERAI_2, GPIO.HIGH)
#    else:
#        GPIO.output(NERAI_1, GPIO.LOW)
#        GPIO.output(NERAI_2, GPIO.LOW)

# --------------------------------
# 設定ボタン
# --------------------------------
# 095
#@webiopi.macro
#def btnSetting():
#    GPIO.output(SET_1, GPIO.HIGH)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.LOW)
#    time.sleep(0.1)
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.LOW)

# --------------------------------
# [↑]ボタン
# --------------------------------
# 095
#@webiopi.macro
#def btnArrUp():
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.HIGH)
#    GPIO.output(SET_3, GPIO.LOW)
#    time.sleep(0.1)
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.LOW)

# --------------------------------
# [↓]ボタン
# --------------------------------
#@webiopi.macro
#def btnArrDown():
#    GPIO.output(SET_1, GPIO.HIGH)
#    GPIO.output(SET_2, GPIO.HIGH)
#    GPIO.output(SET_3, GPIO.LOW)
#    time.sleep(0.1)
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.LOW)

# --------------------------------
# [←]ボタン
# --------------------------------
# 095
#@webiopi.macro
#def btnArrLeft():
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.HIGH)
#    time.sleep(0.1)
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.LOW)

# --------------------------------
# [→]ボタン
# --------------------------------
# 095
#@webiopi.macro
#def btnArrRight():
#    GPIO.output(SET_1, GPIO.HIGH)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.HIGH)
#    time.sleep(0.1)
#    GPIO.output(SET_1, GPIO.LOW)
#    GPIO.output(SET_2, GPIO.LOW)
#    GPIO.output(SET_3, GPIO.LOW)

# --------------------------------
# set point and get environment variable
# --------------------------------
@webiopi.macro
def Game_Initialize(u, s):
    global sess
    global userid
    global credit
    global point
    global evNERAI
    global evCHANCE # 0603
    global evBR_MUTEX
    global jsonkey
    global auto_count # 0310
    global term_flg # 0315
    global error_code
    global chkdt # 816
    global RASPI
    global RPDB
    global start_flg # 0329
    global timer # timer
    start_flg = 0 # 0329
    point = 0
    credit = 0
    auto_count = 0 # 0310
    term_flg = 0 # 0315
    evNERAI = 0
    evCHANCE = 0 # 0603
    evBR_MUTEX = 0
    userid = u
    sess = s
    eeee = 0
    jsonkey = getSessionID()
    try:
        conn = mc.connect(**DNS)
        cur = conn.cursor(prepared=True)
        stmt = "select count(*) from raspi where id<>? and player=?" # 0429 check duplicate
        cur.execute(stmt, (RP_ID, userid))
        record = cur.fetchone()
        if int(record[0]) > 0:
            error_code = ERR_DUP
        else:
#            stmt = "select r.session_id,r.player,u.point,r.btn_nerai,r.br_mutex from raspi r left join users u on r.player=u.id where r.id=? and r.player=? and r.session_id=? and r.<start_date></start_date> between (NOW() - INTERVAL 90 SECOND) and (NOW() + INTERVAL 90 SECOND)"
            stmt = "select r.session_id,r.player,u.point,r.btn_nerai,r.btn_chance,r.br_mutex from raspi r left join users u on r.player=u.id where r.id=? and r.player=? and r.session_id=?"
            cur.execute(stmt, (RP_ID, userid, sess))
            record = cur.fetchone()
            if (record == None):
                printLog(stmt + " ===== rp_id=" + str(RP_ID) + " userid=" + str(userid) + " sess=" + sess) # 3b
                error_code = ERR_RASPI
            else:
                sess = record[0].decode('utf-8')
                userid = record[1]
                credit = record[2]
                evNERAI = record[3]
                evCHANCE = record[4] # 0603
                evBR_MUTEX = record[5]
#                stmt = "select `point` from `raspi_history` where raspi_id=? and user_id=? and session_id=? and `date` between (NOW() - INTERVAL 90 SECOND) and (NOW() + INTERVAL 90 SECOND) order by `date` desc"
                stmt = "select `point` from `raspi_history` where raspi_id=? and user_id=? and session_id=? order by `date` desc"
                cur.execute(stmt, (RP_ID, userid, sess))
                record = cur.fetchone()
                if (record == None):
                    error_code = ERR_HISTORY
#                if int(credit) == int(record[0]):
#                    start_flg = 1 # 0329
#                    RPDB.setPoint(credit)
#                    RPDB.initDb()
#                else:
#                    error_code = ERR_POINT # DB_ERROR
#                    printLog('- ERROR - credit=' + str(credit) + ' record[0]=' + str(record[0]))
                else:
                    start_flg = 1 # 0329
                    RPDB.setPoint(credit)
                    RPDB.initDb()
    except mc.Error as e:
        eeee = 1
        printLog('- ERROR - ppppp ' + e.msg)
    finally:
        cur.close
        conn.close
    chkdt = datetime.now() # 816
    timer.setTimer(12) # timer start
    dict = { 'day': datetime.now().strftime("%Y/%m/%d %H:%M:%S"), 'sid': sess, 'jsonkey': jsonkey, 'uid': int(userid), 'credit': int(credit), 'error': int(error_code) }
    f = open(start, 'w')
    json.dump(dict, f)
    printLog('- INFO - Game start - uid:' + str(userid) + ' sid:' + sess + ' point:' + str(credit) + ' error:' + str(error_code))
    return str(error_code)

# --------------------------------
# RASPI情報取得
# --------------------------------
@webiopi.macro
def getInfo(uid):
    return "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (str(RP_ID), evNAME, str(evNERAI), str(evCHANCE), evHOME, evMOMO + ":" + str(evPORT_VIDEO), evTIME_OUT, evOPEN_TIME, evCLOSE_TIME, str(evAG_MAX))

# --------------------------------
# 状態取得
# --------------------------------
@webiopi.macro
def getStatus(uid):
    global chkdt # 816
    global jsonkey # 816
    global error_code # 816
    global RPDB #class
    global start_flg # 0329
#    if abs(credit - RPDB.getPoint()) > 3:
#    if start_flg == 1 and credit != RPDB.getPoint(): # 0329
    if start_flg == 1 and credit != RPDB.getPoint() and credit > 2: # 098
        RPDB.setPoint(credit)
        RPDB.updateDb(point)
    if chkdt != 0:
        chkdt = datetime.now() # 816
    dict = { 'day': datetime.now().strftime("%Y/%m/%d %H:%M:%S"), 'sid': sess, 'jsonkey': jsonkey, 'rid': int(RP_ID), 'uid': int(userid), 'credit': int(credit), 'point': int(point), 'game': int(gmCount), 'rb': int(rbCount), 'bb': int(bbCount), 'bw': int(bwCount) }
    f = open(output, 'w')
    json.dump(dict, f)
    return "%s,%s,%s,%s,%s,%s,%s,%s" % (credit, game, st_ap, st_rb, st_bb, st_ct, auto_count, error_code) # 0310

# --------------------------------
# DB更新
# --------------------------------
@webiopi.macro
def Game_Finalize(*argc):
    global term_flg # 0315
    global error_code
    global chkdt # 816
    global jsonkey # 816
    global RPDB
    global point #091
    global credit #091
    if (int(term_flg) > 0):
        return None
    opt = argc[0]
    io = 0
    if len(argc) == 2:
        io = argc[1]
    try:
        conn = mc.connect(**DNS)
        cur = conn.cursor(prepared=True)
        stmt = "select point from users where id=?"
        cur.execute(stmt, (userid,))
        record = cur.fetchone()
        if (record == None):
            error_code = ERR_USER
        day = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        # ラスパイ履歴
# 816        stmt = "insert into raspi_history (raspi_id,user_id,operator,io,`point`,`date`,session_id,json_id) values (?,?,null,0,?,now(),?,?)"
# 816        cur.execute(stmt, (RP_ID, userid, point, sess, jsonkey))
        stmt = "insert into raspi_history (raspi_id,user_id,operator,io,`point`,`date`,session_id,json_id) values (?,?,null,?,?,now(),?,?)"
        cur.execute(stmt, (RP_ID, userid, io, point, sess, jsonkey))
        conn.commit()
        if int(opt) == 0 or int(opt) == 1:
            # ユーザー履歴
            RPDB.termDb(point)
        # ラズパイをオンライン状態に
        if (int(error_code) != 0): #maintenance
            RPDB.setStatus(4)
        else:
            if int(opt) == 1: # 保留
                stmt = "update raspi set start_date=now(),status=3 where id=?" # 0329
            else: # 終了
                stmt = "update raspi set status=1,player=null,start_date=null,session_id=null,json_id=null where id=?"
            cur.execute(stmt, (RP_ID,))
            conn.commit()
            term_flg = int(term_flg) + 1 # 0315
    except mc.Error as e:
        printLog('- ERROR - ' + e.msg)
    finally:
        cur.close
        conn.close
    GPIO.output(NERAI_1, GPIO.LOW)
    GPIO.output(NERAI_2, GPIO.LOW)
    GPIO.output(AUTO, GPIO.LOW)
    GPIO.output(ENABLE, GPIO.LOW)
    point = 0 #091
    credit = 0 #091
    chkdt = 0 # 816
    error_code = 0 #0116
    jsonkey = '' # 816
    dict = { 'day': day, 'sid': sess, 'jsonkey': jsonkey, 'rid': int(RP_ID), 'uid': int(userid), 'credit': int(credit), 'point': int(point), 'game': int(gmCount), 'rb': int(rbCount), 'bb': int(bbCount), 'bw': int(bwCount), 'error': int(error_code) }
    f = open(stop, 'w')
    json.dump(dict, f)
# 816        printLog('- INFO - Game stop - uid:' + str(userid) + ' sid:' + sess + ' point:' + str(credit) + ' credit:' + str(point) + ' error:' + str(error_code))
    printLog('- INFO - Game stop - io:' + str(io) + ' uid:' + str(userid) + ' sid:' + sess + ' point:' + str(credit) + ' credit:' + str(point) + ' error:' + str(error_code))


@webiopi.macro
def Game_Finalize2(opt):
    global term_flg # 0315
    global error_code
    global chkdt # 816
    global jsonkey # 816
    global RPDB
    global point #091
    global credit #091
    try:
        conn = mc.connect(**DNS)
        cur = conn.cursor(prepared=True)
        if int(opt) == 1: # 保留
            stmt = "update raspi set start_date=now(),status=3 where id=?" # 0329
        else: # 終了
            stmt = "update raspi set status=1,player=null,start_date=null,session_id=null,json_id=null where id=?"
        cur.execute(stmt, (RP_ID,))
        conn.commit()
        term_flg = int(term_flg) + 1 # 0315
    except mc.Error as e:
        printLog('- ERROR - ' + e.msg)
    finally:
        cur.close
        conn.close
    GPIO.output(NERAI_1, GPIO.LOW)
    GPIO.output(NERAI_2, GPIO.LOW)
    GPIO.output(AUTO, GPIO.LOW)
    GPIO.output(ENABLE, GPIO.LOW)



@webiopi.macro
def testMacro(r):
    return "沖ドキ バカンスパネル"

# --------------------------------
# 再起動
# --------------------------------
@webiopi.macro
def doReboot():
    os.system('reboot')
