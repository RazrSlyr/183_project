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

    app.methods = {
        add_chat: app.add_chat,
    };

    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });


    app.init = () => {
        app.update_chat();  // MP:  Start updater/set_interval
    };

    app.init();
};

init(app);