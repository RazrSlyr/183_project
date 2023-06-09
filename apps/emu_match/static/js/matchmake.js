// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};

// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        // Complete as you see fit.
        match: null,
        in_queue: false,
    };

    app.check_interval = null;

    // RV: check for a match
    app.check_match = function () {
        if (app.vue.match !== null) return;
        axios.get(check_url).then((response) => {
            // RV: Check response data
            let data = response.data;
            if (data["found"]) {
                clearInterval(app.checkInterval);
                // RV: Goes to lobby
                document.location.href = data["url"];
            }
        });
    }

    app.leave_queue = function () {
        axios.get(leave_url).then((response) => {
            // RV: You have left the queue, redirect to games page
            document.location.href = response.data["url"];
        })
    }


    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        leave_queue: app.leave_queue
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {
        app.check_match();
        app.checkInterval = setInterval(app.check_match, 1000);
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code in it. 
init(app);
