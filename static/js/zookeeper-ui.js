$(function() {
    $('#create_button').click(function() {
        var new_znode_name = $('#new_znode_name').val();
        var new_znode_data = $('#new_znode_data').val();
        $.ajax({
            url: '/create',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
                alert("Node created.");
                location.reload(true);
            },
            error: function(error) {
                console.log(error);
                alert("I have error: " + error)
            }
        });
    });
});

function delete_znode(str) {
    delete_znode = "/" + str;
    if (confirm("Are you sure you want to delete " + delete_znode + " ?")) {
        $.ajax({
            url: '/delete',
            data: "delete_znode=" + delete_znode,
            type: "POST",
            success: function(response) {
                alert("Znode " + delete_znode + " has been deleted!");
                location.reload(true);
            },
            error: function(error) {
                console.log(error);
                alert("I have error: " + error)
            }
        });
    } else {
        return false;
    }
}

function f_modify_znode(m_node_name){
    m_node_name_g = m_node_name;
    console.log(m_node_name_g);
}
$(function() {
    $('#modify_button').click(function() {
        var new_znode_data_modify = $('#new_znode_data_modify').val();
        var node_name = m_node_name_g;
        $.ajax({
            url: '/modify',
            data: "new_znode_data_modify=" + new_znode_data_modify + "&node_name=/" + node_name,
            type: 'POST',
            success: function(response) {
                console.log($('form').serialize());
                alert("Node modifed.");
                location.reload(true);
            },
            error: function(error) {
                console.log(error);
                alert("I have error: " + error)
            }
        });
    });
});

function choice_cluster(cluster){
    console.log(cluster);
    $.ajax({
        url: '/clusters',
        data: "cluster=" + cluster,
        type: "POST",
        success: function(response) {
            console.log(response);
            window.location.replace("/");
            },
        error: function(error) {
            console.log(error);
            alert("I have error: " + error)
        }
    });
}
