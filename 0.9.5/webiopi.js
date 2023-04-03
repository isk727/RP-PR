var auto = 0;
var agct = 0;
var xct = 0;
var nerai1 = 0; var nerai2 = 0; var nerai3 = 0;
const bg_on = "#ffa84c"; const bg_off = "#ababab";
const bb_on = "solid 3px #cca84c"; const bb_off = "solid 3px #cdcdcd";
const cl_on = "rgba(200, 120, 12, 1)"; const cl_off = "rgba(12, 12, 12, 1)";
const err_connection = 808;
var exit = 0
const intervalId = setInterval(() =>{
    getStatus();
    if(exit > 0){　
      clearInterval(intervalId);
    }}, 1000);

const exitConf = (opt) => {
	exit = 1;
    $('#opt').val(opt);
    webiopi().callMacro("setActive", 0);
    webiopi().callMacro("Game_Finalize", [opt,], callbackExitConf);
};
//function exitConf(opt) {
//	$('#opt').val(opt);
//	webiopi().callMacro("Game_Finalize", [opt,], callbackExitConf);
//}

function callbackExitConf(macro, args, data) {
	$('#article1').fadeOut( 1000 );
	setTimeout(function(){
		$('#article2').css({'display':'block'});
	},2000);
	setTimeout(function(){
		$('#frm').submit();
	},2000);
}

function exitConf1(opt) {
	webiopi().callMacro("Game_Finalize", [opt,]);
	$('#article1').fadeOut( 3000 );
//	$('#article1').css({'display':'none'});
	$('#article2').css({'display':'block'});
	setTimeout(function(){
		$('#opt').val(opt);
		$('#frm').submit();
	},13000);
}

function exitConf2(opt) {
	webiopi().callMacro("Game_Finalize", [opt,]);
//	webiopi().callMacro("dataUpdate", [point, uid, rid]);
//	if (auto == 1) {
//		swal("AUTOを終了させてください");
//		return false;
//	}
	$('#opt').val(opt);
	$('#frm').submit();
//	window.location.href = url;
}

function exitConf3(url) {
	webiopi().callMacro("dataUpdate", [point, uid, rid]);
//	if (auto == 1) {
//		swal("AUTOを終了させてください");
//		return false;
//	}
	window.location.href = url;
}



function neraiOff() {
//    $('#neraiButton1').css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
//    $('#neraiButton2').css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
//    $('#neraiButton3').css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
}

function btnAutoClick(obj) {
    if (auto == 1) {
        auto = 0;
//        $(obj).css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
        $(obj).css('background','url(../img/btn-auto-0.png) left top no-repeat');
    } else {
//        $(obj).css({'background':bg_on,'border-bottom':bb_on,'color':cl_on});
        $(obj).css('background','url(../img/btn-auto-1.png) left top no-repeat');
        auto = 1;
    }
}

function btnNerai1Click(obj) {
    if (nerai1 == 1) {
        nerai1 = 0;
        //$(obj).css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
        $(obj).css('background','url(../img/btn-nerai-0.png) left top no-repeat');
    } else {
        neraiOff();
        //$(obj).css({'background':bg_on,'border-bottom':bb_on,'color':cl_on});
        $(obj).css('background','url(../img/btn-nerai-1.png) left top no-repeat');
        nerai1 = 1;
        nerai2 = 0;
        nerai3 = 0;
    }
}

function btnNerai2Click(obj) {
    if (nerai2 == 1) {
        $(obj).css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
        nerai2 = 0;
    } else {
        neraiOff();
        $(obj).css({'background':bg_on,'border-bottom':bb_on,'color':cl_on});
        nerai1 = 0;
        nerai2 = 1;
        nerai3 = 0;
    }
}

function btnNerai3Click(obj) {
    if (nerai3 == 1) {
        $(obj).css({'background':bg_off,'border-bottom':bb_off,'color':cl_off});
        nerai3 = 0;
    } else {
        neraiOff();
        $(obj).css({'background':bg_on,'border-bottom':bb_on,'color':cl_on});
        nerai1 = 0;
        nerai2 = 0;
        nerai3 = 1;
    }
}

function getStatus() { webiopi().callMacro("getStatus", 2, callbackGetStatus); }

function RaspiStatus(data) {
    let resArray = data.split(",");
    this.credit = resArray[0];
    this.game = resArray[1];;
    this.st_ap = resArray[2];;
    this.st_rb = resArray[3];;
    this.st_bb = resArray[4];;
    this.st_ct = resArray[5];;
    this.auto_count = resArray[6];;
    this.error_code = resArray[7];;
}

function callbackGetStatus(macro, args, data) {
    let st = new RaspiStatus(data);
    xct++;
//    $('#debug').html("[" + st.error_code + "]");
//$('#debug').html("x=" + xct + " [" + st.error_code + "]");
    if (st.error_code != 0) {
//        if (st.error_code == err_connection) {
        // 強制脱出
//                    $('#opt').val(1);
//                    $('#frm').submit();
//        } else {
            exitConf(st.error_code);
//        }
    }
    $("#info").html(`POINT : ${st.credit} | GAME : ${st.game}`);
    point = Number(st.credit);
    agct = Number(st.auto_count);
	if (agct > ag_max) {
		exitConf(1);
	}
    if (st.st_rb == "1") $('#rb_on').css({ 'visibility': 'visible' });
    else $('#rb_on').css({ 'visibility': 'hidden' });
    if (st.st_bb == "1") $('#bb_on').css({ 'visibility': 'visible' });
    else $('#bb_on').css({ 'visibility': 'hidden' });
    if (point > 0) {
        webiopi().callMacro("setActive", 1);
    } else {
        webiopi().callMacro("setActive", 0);
    }
}