let app = {};

let init = (app) => {


    app.data = {
        chat_list: [], // MP: all chats
        new_chat: "",  // MP:  new chat
    };

    app.enumerate = (a) => {        
        let k = 0;
        a.map((e) => { e._idx = k++; });
        return a;
    };

    // MP:  Set interval for get_chat()
    app.update_chat = function () {
        app.checkInterval = setInterval(app.get_chat, 1000);
    }

    // MP:  Get all chats
    app.get_chat = function () {
        axios.get(get_chat_url).then((response) => {            
            app.vue.chat_list = [];            
                response.data.chats.forEach(element => {
                    // MP:  console.log(element.email, element.time, element.chat);                    
                    app.vue.chat_list.push({
                        email: element.email,
                        time: element.time,
                        chat: element.chat,
                    });
                });            
        });
    }

    // MP:  Add new chat
    app.add_chat = function (chat) {
        axios.post(add_chat_url, {
            chat: chat,
        }).then(function (response) {            
        });

        app.vue.chat_list.push(chat);   // MP:  Add to chat list
        app.vue.new_chat = "";          // MP:  Clear new chat
    }

    app.check_lobby = function() {
        if (check_lobby_url === undefined) return;
        axios.get(check_lobby_url).then((response) => {
            // RV: if the message is anything other than OK, leave
            let message = response.data["message"];
            if (message != "OK") {
                document.location.href = response.data["url"];
            }
        })
    }

    // RV: close the lobby
    app.close_lobby = function() {
        if (close_lobby_url === undefined) return;
        axios.get(close_lobby_url).then((response) => {
            // RV: Lobby has been closed, go back to url
            console.log(response.data);
            document.location.href = response.data["url"];
        })
    }

    app.methods = {
        add_chat: app.add_chat,
        close_lobby: app.close_lobby
    };

    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });


    app.init = () => {
        app.update_chat();  // MP:  Start updater/set_interval
        setInterval(app.check_lobby, 1000); // RV: Start checking lobby status
    };

    app.init();
};

init(app);