import $ from 'jquery';
import 'bootstrap';
import 'bootstrap/dist/css/bootstrap.css';
import 'font-awesome/css/font-awesome.css';
// Chainbot functions

// start game
export function startGame()
{
    if (!$("#game-start-btn").hasClass("disabled")) {
        $("#game-status").load("/control/gbegin");
        setTimeout(function(){
            window.location.reload(true);
        });
    }
}

// stop game
export function stopGame()
{
    if (!$("#game-stop-btn").hasClass("disabled")) {
        $.ajax({
            method: "GET",
            url: "/control/gend"
        });
    }
}

// check whether game can be started
function canStartGame()
{
    $.ajax({
        method: "GET",
        url: "/status/can_start",
        success: function(result) {
            if (result.status == "ok") {
                if (result.can_start) {
                    $("#game-start-btn").removeClass("disabled");
                }
                else {
                    $("#game-start-btn").addClass("disabled");
                }
            }
        }});
}

// start refreshing view
export var refreshTimer;
export function startRefreshing()
{
    // refresh immediately
    refreshStatus();
    refreshTimer = setInterval(refreshStatus, 1000);
}

// stop refreshing view
function stopRefreshing()
{
    clearInterval(refreshTimer);
}

export function activateTournament(){
    var tournament_id;
    tournament_id = $("#tournament-selector").find(":selected").attr("data");
    $.ajax({method: "GET", url: "/control/activateTournament/"+tournament_id});
    // reload
    window.location.reload(true);
}

export function deactivateTournament(){
    $.ajax({method: "GET", url: "/control/deactivateTournament"});
}

// retrieve current player names
function updatePlayerNames(players) {
    $.each(players, function(key, val) { $("#pline-"+key).text(val.web_txt); });
}

// update local registry
export function updateRegistry() {
    $.ajax({method: "GET",
            url: "/cbcentral/update",
            success: function() {
                window.location.reload(true);
            }
           });
}
// perform full refresh of view
var currentGameStatus;
var lastGameStatus = "stopped";
var lastGameData;
function refreshStatus()
{
    $.ajax({
        method: "GET",
        url: "/status/game",
        success: function(result) {
            if (result.status == "ok") {
                // update status globally
                lastGameData = result;
                currentGameStatus = result.game;
                // update player names
                updatePlayerNames(result.players);
                // manage tournament toggler
                if (!result.tournament)
                {
                    $("#tournament-toggle").text("Activate tournament");
                    $("#tournament-toggle").attr("data-toggle", "modal");
                    $("#tournament-toggle").attr("data-target", "#tournamentModal");
                    $("#tournament-toggle").click(null);
                    $("#tournament-name").text("");
                    $("#tournamentDropdown").addClass("disabled");
                    var p;
                    for(p=0;p<4;p++) {
                        $("#player-add-"+p).removeClass("disabled");
                    }
                }
                else
                {
                    if (lastGameStatus != currentGameStatus)
                    {
                        if (currentGameStatus == "stopped")
                        {
                            // update
                            updateRegistry();
                        }
                        lastGameStatus = currentGameStatus;
                    }
                    $("#tournament-toggle").text("Deactivate tournament");
                    $("#tournament-toggle").removeAttr("data-toggle");
                    $("#tournament-toggle").removeAttr("data-target");
                    $("#tournament-toggle").click(deactivateTournament);
                    $("#tournament-name").text(result.tournament_str);
                    $("#tournamentDropdown").removeClass("disabled");
                    var p;
                    for(p=0;p<4;p++) {
                        if (!result.game_id) {
                            $("#player-add-"+p).addClass("disabled");
                        }
                        else
                        {
                            $("#player-add-"+p).removeClass("disabled");
                        }
                    }
                }
                if (result.game != "stopped" && result.game != "finished") {
                    // set scores
                    $.each(result.scores,
                           function(key, val) {
                               if (key != "status") {
                                   updateScore(key, val, result.serving);
                               }
                           });

                    var gameStr = "";
                    if (result.game == "started")
                    {
                        gameStr = "Game Started";
                    }
                    else
                    {
                        gameStr = "Game Paused";
                    }

                    if (result.game_seq != null)
                    {
                        gameStr += " ["+result.game_seq+"]";
                    }
                    $("#game-status").text(gameStr);
                    // enable pause/stop
                    $("#game-stop-btn").removeClass("disabled");
                    $("#game-pause-btn").removeClass("disabled");
                    $("#game-start-btn").addClass("disabled");
                    $("#game-select-trigger").addClass("disabled");
                    $("#registry-update-trigger").addClass("disabled");
                    var minutes = Math.floor(result.remaining_time/60);
                    var seconds = result.remaining_time - minutes*60;
                    function str_pad_left(string,pad,length) {
                        return (new Array(length+1).join(pad)+string).slice(-length);
                    }
                    var finalTime = str_pad_left(minutes,'0',2)+':'+str_pad_left(seconds,'0',2);
                    $("#game-timer").text(finalTime);
                    // disable dropdown in player names
                    var p;
                    for (p=0;p<4;p++) {
                        $("#pline-"+p+"-drop").addClass("disabled");
                        // disable controls if player not active in game
                        if ((!result.players[p].registered) || (result.scores[p] == -10)) {
                            disableControls(p);
                            // also disable serve button
                            $("#pline-"+p).addClass("disabled");
                        }
                    }

                    $("#tournament-toggle").addClass("disabled");
                }
                else {
                    if (result.game == "finished")
                    {
                        //update scores
                        var high_score = -10;
                        var winner = null;
                        $.each(result.scores,
                               function(key, val) {
                                   if (key != "status") {
                                       if (val > high_score)
                                       {
                                           high_score = val;
                                           winner = key;
                                       }
                                       updateScore(key, val, result.serving);
                                   }
                               });
                        if (winner != null)
                        {
                            $("#pline-"+p).addClass("btn-success");
                        }
                    }
                    else
                    {
                        canStartGame();
                    }
                    var p;
                    for (p=0; p<4; p++) {
                        disableControls(p);
                        // enable dropdowns in player names
                        $("#pline-"+p+"-drop").removeClass("disabled");
                        $("#pline-"+p).removeClass("btn-danger");
                        $("#pline-"+p).removeClass("disabled");
                        $("#pline-"+p+"-drop").removeClass("btn-danger");
                    }
                    $("#game-select-trigger").removeClass("disabled");
                    $("#registry-update-trigger").removeClass("disabled");
                    $("#game-stop-btn").addClass("disabled");
                    $("#game-pause-btn").addClass("disabled");
                    $("#tournament-toggle").removeClass("disabled");
                    $("#game-status").text("Game not in progress");
                }
            }
        }
    });
}

// refresh score in view
function updateScore(player, score, serving)
{
    if (serving != player) {
        $("#pline-"+player).removeClass("btn-danger");
        $("#pline-"+player).removeClass("btn-success");
        $("#pline-"+player+"-drop").removeClass("btn-danger");
    }
    else
    {
        $("#pline-"+player).addClass("btn-danger");
        $("#pline-"+player+"-drop").addClass("btn-danger");
    }

    $("#scoreDropdownBtn"+player).text(score);
}

// set turn manually
export function setTurn(playerNum)
{
    if (currentGameStatus != "started")
    {
        return;
    }
    if (!lastGameData.players[playerNum].registered || lastGameData.scores[playerNum] == -10)
    {
        return;
    }
    $.ajax({
        method: "GET",
        url: "/control/setturn/"+playerNum
    });
}

// set score manually
export function setScore(playerNum, score)
{
    if (currentGameStatus != "started")
    {
        return;
    }
    if (!lastGameData.players[playerNum].registered || lastGameData.scores[playerNum] == -10)
    {
        return;
    }
    $.ajax({
        method: "GET",
        url: "/control/setscore/"+playerNum+","+score
    });
}


// trigger a scoring event
export function scoringEvt(playerNum, evtType)
{
    if (currentGameStatus != "started")
    {
        return;
    }
    if (!lastGameData.players[playerNum].registered || lastGameData.scores[playerNum] == -10)
    {
        return;
    }
    $.ajax({
        method: "GET",
        url: "/control/event/"+playerNum+","+evtType
    });
}

// disable referee controls for player
function disableControls(playerNum)
{
    var evt;
    for (evt = 0; evt < 8; evt++) {
        $("#p"+playerNum+"Evt"+evt).addClass("disabled");
        $("#scoreDropdownBtn"+playerNum).addClass("disabled");
    }
}


// enable referee controls for a player
function enableControls(playerNum)
{
    var evt;
    for (evt = 0; evt < 8; evt++) {
        $("#p"+playerNum+"Evt"+evt).removeClass("disabled");
        $("#scoreDropdownBtn"+playerNum).removeClass("disabled");
    }
}

export function addPlayer() {
    var player_id_element, player_id, player_num;
    player_id_element = $("#player-selector").find(":selected");
    player_id = player_id_element.attr("data");
    player_num = $("#player-selector").attr("curplayernum");

    //in case of success, disable the entry
    $.ajax({
        method: "GET",
        url: "/control/pregister/"+player_num+","+player_id,
        success: function() {
            window.location.reload(true);
        }
    });
}

export function rmPlayer(playerNum) {
    $.ajax({
        method: "GET",
        url: "/control/punregister/"+playerNum,
        success: function() {
            window.location.reload(true);
        }
    });
}
function pairRemote(playerNum) {}



export function activateGame(){
    var game_id;
    game_id = $("#game-selector").find(":selected").attr("data");
    $.ajax({method: "GET", url: "/control/activateGame/"+game_id});
    // reload
    window.location.reload(true);
}

window.$ = $;
