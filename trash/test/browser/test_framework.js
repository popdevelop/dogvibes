//if (!('WebSocket' in window)) {
//    alert('WebSocket not available in your browser. Use Google Chrome')
//}



var Log = function(){
    this.error = function(msg) {
        document.getElementById("log").innerHTML += '<font color="red"><b>' + msg + '</b></font>' + '<br>';
    };
    this.reply = function(name, color, msg) {
        document.getElementById('log').innerHTML += '&nbsp; <font color="' + color + '"><i>' + msg + '</i></font><br>';
    };
    this.command = function(name, color, msg) {
        document.getElementById('log').innerHTML += '<font color="' + color + '"><b>' + msg + '</b></font><br>';
    };
    this.result = function(color, command, reply, startTime, endTime, firstTime) {
        document.getElementById("log").innerHTML += '<font color="' + color + '"><b>'+command+'</b><br>'+(startTime-firstTime) + 'ms' + ' (' + (endTime-startTime) +'ms): '+reply+'<i></i></font><br>';
    };
    return this;
}
var log = new Log();

var testers = [];

colors_nbr = 0;
colors = []
colors[0] = '#ff0000'
colors[1] = '#0000ff'
colors[2] = '#00dd00'
colors[3] = '#ffff00'

var lastCmdTime = 0;
var nbrTotalCommands = 0;
var nbrTotalReplies = 0;
var nbrReplyPass = 0;
var nbrReplyFail = 0;

var queuedCommands = [];

function check(expr) {
    if (expr === true) {
        nbrReplyPass++;
    } else {
        nbrReplyFail++;
    }
}

function pushHandler(d) {
    // dummy
}


this.sendQueuedCmd = function(queuedCommand) {

    var params = queuedCommand.command.params;
    var tester = queuedCommand.tester;

    if (params['cmd'].indexOf('?') == -1) {
        params['cmd'] += "?msg_id=" + tester.msg_id;
    } else {
        params['cmd'] += "&msg_id=" + tester.msg_id;
    }
    var t = new Date().getTime();
    var lastCmdTime = t;
    if (tester.firstTime == 0)
        tester.firstTime = t;

    if (params['requires'] !== undefined) {
        extraParam = params['requires'] + '=' + eval(params['requires'])
        if (params['cmd'].indexOf('?') == -1) {
            params['cmd'] += '?' + extraParam;
        } else {
            params['cmd'] += '&' + extraParam;
        }
    }
    log.command(tester.name, tester.color, params['cmd'])

    var request = { c: params['cmd'],
                    t: t,
                    i: tester.msg_id }

    tester.replyCallbacks.push({ msg_id: tester.msg_id,
                               params: params });

    tester.commands.push(request);

//    queuedCommands.push({command: request, tester: tester})

    tester.ws.send(params['cmd']);
    tester.msg_id++;

    blocking = true;
}

function Tester(name, uri)
{
    this.name = name;
    this.color = colors[colors_nbr];

    this.msg_id = 0;

    this.ws = new WebSocket(uri);
    this.ws.parent = this;

    this.commands = []
    this.replies = []

    this.replyCallbacks = []

    this.firstTime = 0;

//    function getAllPlaylists(json) {
//        //document.getElementById('log').innerHTML += json['result'][0]['name'] + '<br>';
//    }

    this.replyParamsFromMsgId = function(msg_id) {
        for (var i = 0; i < this.replyCallbacks.length; ++i) {
            if (msg_id == this.replyCallbacks[i].msg_id) {
                return this.replyCallbacks[i].params;
            }
        }
    }

    this.ws.onopen = function() {};
    this.ws.onclose = function() {};
    this.ws.onmessage = function (e) {
        var reply = eval('('+e.data+')');
        var t = new Date().getTime()
        this.parent.replies.push({c: e.data, t: t, i: reply.msg_id});
        nbrTotalReplies++;
        log.reply(this.parent.name, this.parent.color, e.data)

        var params = this.parent.replyParamsFromMsgId(reply.msg_id)
        if (params['onReply'] !== undefined)
            params.onReply(reply);

        blocking = false;
    };

    this.sendCmd = function(params) {
//        if (params['cmd'].indexOf('?') == -1) {
//            params['cmd'] += "?msg_id=" + this.msg_id;
//        } else {
//            params['cmd'] += "&msg_id=" + this.msg_id;
//        }
        var t = new Date().getTime();
//        var lastCmdTime = t;
//        if (this.firstTime == 0)
//            this.firstTime = t;
//
//        log.command(this.name, this.color, params['cmd'])
//
        var request = { c: params['cmd'],
                        t: t,
                        i: this.msg_id,
                        params: params }
//
//        this.replyCallbacks.push({ msg_id: this.msg_id,
//                                   params: params });
//
//        this.commands.push(request);
//
//        nbrTotalCommands++;

        nbrTotalCommands++;
//        if (params['prepend'] == true) {
//            queuedCommands.unshift({command: request, tester: this})
//        } else {
            queuedCommands.push({command: request, tester: this})
//        }

//        this.ws.send(params['cmd']);
//        this.msg_id++;
    }

    testers.push(this);
    colors_nbr++;

    return this;
}

function waitForCompletion() {
    if (nbrTotalCommands != nbrTotalReplies) {
        setTimeout('waitForCompletion()', 0);
        //document.getElementById("log").innerHTML += 'waiting...';
    } else {
        document.getElementById("log").innerHTML += 'Pass: ' + nbrReplyPass + '<br>';
        document.getElementById("log").innerHTML += 'Fail: ' + nbrReplyFail + '<br>';
    }
}

queueCount=0;
blocking=false;
function executeQueuedCommands() {
//    for (var i = 0; i < queuedCommands.length; ++i) {
    if (queueCount < queuedCommands.length) {
        if (blocking == true) {
            setTimeout('executeQueuedCommands()', 100);
        } else {
            sendQueuedCmd(queuedCommands[queueCount]);
            queueCount++;
            executeQueuedCommands();
        }
    }
}

function start() {
    for (var i = 0; i < testers.length; ++i) {
        if (testers[i].ws.readyState != WebSocket.OPEN) {
            log.error('Could not open WebSocket');
            return;
        }
    }
    run();

    executeQueuedCommands()

    waitForCompletion();
}

function initTest() {
    setTimeout('start()', 500);
}

function findReplyFromCommand(command) {
    for (var j = 0; j < testers.length; ++j) {
        var t = testers[j];
        for (var i = 0; i < t.replies.length; ++i) {
            if (command.i == t.replies[i].i) {
                return t.replies[i]
            }
        }
    }
    return null;
}
function showResults() {
    setTimeout('x_showResults()', 2000);
}
function x_showResults() {
    document.getElementById("log").innerHTML += '<h3>Results</h3>';
    for (var j = 0; j < testers.length; ++j) {
        var t = testers[j];
        for (var i = 0; i < t.commands.length; ++i) {
            var command = t.commands[i];
            var reply = findReplyFromCommand(command);
            if (reply == null)
                alert("Did not recieve reply! (Write test for this)");
            log.result(t.color, command.c, reply.c, command.t, reply.t, t.firstTime);
        }
    }
}
