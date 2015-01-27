#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'spooner'

from kazoo.client import KazooClient
from flask import Flask, render_template, request, session
import logging
import yaml
import datetime
import re
import json

logging.basicConfig(format=u'%(filename)s %(funcName)20s()[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)


app = Flask(__name__)
app.secret_key = '[\xaf\xbd\x1dV\xb5#\x80\xff\xa7\x9a1p\xb1\xc4\x99\x07X\xa0\xb9W5\xfdC'


@app.route('/')
def index():
    path = "/"
    render_list = []
    breadcrumb_list = []
    try:
        zk_conf = get_clusters()
        root_znodes = ZkWork().zk_get_children(path)
        for i in root_znodes:
            render_dict = {}
            render_dict["node"] = i
            render_dict["data"], state = ZkWork().get_state(path + "/" + i)
            render_dict["mtime"] = datetime.datetime.fromtimestamp(state.mtime / 1000).strftime('%Y-%m-%d %H:%M:%S')
            render_dict["ctime"] = datetime.datetime.fromtimestamp(state.ctime / 1000).strftime('%Y-%m-%d %H:%M:%S')
            render_list.append(render_dict)
    except Exception as e:
        logging.exception(e)
        return render_template("5xx.html")
    return render_template("index.html", znodes=render_list, breadcrumb_list=breadcrumb_list, now_path=path, zk_conf=zk_conf)


@app.route('/view/<path:path>')
def next_znode(path):
    render_list = []
    breadcrumb_render_list = []
    previous_znode = ''
    breadcrumb_list = re.split("/", path)
    now_path = "/" + path + "/"
    try:
        zk_conf = get_clusters()
        root_znodes = ZkWork().zk_get_children(path)
        for znode in breadcrumb_list:
            breadcrumb_dict = {}
            breadcrumb_dict["url"] = "/view" + previous_znode + "/" + znode
            breadcrumb_dict["name"] = znode
            breadcrumb_render_list.append(breadcrumb_dict)
            previous_znode += "/" + znode
        for i in root_znodes:
            render_dict = {}
            render_dict["breadcrumb"] = re.split("/", path)
            render_dict["node"] = path + "/" + i
            render_dict["data"], state = ZkWork().get_state(path + "/" + i)
            render_dict["mtime"] = datetime.datetime.fromtimestamp(state.mtime / 1000).strftime('%Y-%m-%d %H:%M:%S')
            render_dict["ctime"] = datetime.datetime.fromtimestamp(state.ctime / 1000).strftime('%Y-%m-%d %H:%M:%S')
            render_list.append(render_dict)
    except Exception as e:
        logging.exception(e)
        return render_template("5xx.html")
    return render_template("index.html", znodes=render_list, breadcrumb_list=breadcrumb_render_list, now_path=now_path, zk_conf=zk_conf)


@app.route('/create', methods=['POST'])
def create():
    try:
        new_znode_name = request.form['new_znode_name']
        new_znode_data = request.form['new_znode_data']
        ZkWork().set_state(new_znode_name, str(new_znode_data))
        return json.dumps({'status': 'OK'})
    except Exception as e:
        logging.exception(e)
        return render_template("5xx.html")


@app.route('/modify', methods=['POST'])
def modify():
    try:
        new_znode_data = request.form['new_znode_data_modify']
        new_znode_path = request.form['node_name']
        ZkWork().set_state(new_znode_path, str(new_znode_data))
        return json.dumps({'status': 'OK'})
    except Exception as e:
        logging.exception(e)
        return render_template("5xx.html")


@app.route('/delete', methods=['POST'])
def delete():
    try:
        delete_znode = request.form['delete_znode']
        ZkWork().delete_path(str(delete_znode))
        return json.dumps({'status': 'OK'})
    except Exception as e:
        logging.exception(e)
        return render_template("5xx.html")


@app.route('/clusters', methods=['POST'])
def clusters():
    try:
        session['cluster'] = request.form['cluster']
        return json.dumps({'status': 'OK'})
    except Exception as e:
        logging.exception(e)
        return render_template("5xx.html")


def get_clusters():
    zk_conf = []
    try:
        with open("config/zookeeper.yaml", "r") as yaml_zk_conf:
            zk_conf = yaml.load(yaml_zk_conf)
            yaml_zk_conf.close()
    except IOError as e:
        logging.exception(e)
        exit(0)
    return zk_conf


class ZkWork:
    def zk_connect(self, read_only_zk):
        if 'cluster' not in session:
            session['cluster'] = 'development'
        try:
            zk_conf = get_clusters()
            zk_servers = zk_conf[session['cluster']]
            self.zk_conn = KazooClient(hosts=zk_servers, read_only=read_only_zk)
            self.zk_conn.start()
        except Exception as e:
            logging.exception(e)
            self.zk_stop()
            exit(0)


    def zk_stop(self):
        self.zk_conn.stop()
        self.zk_conn.close()


    def set_state(self, children, state):
        self.zk_connect("False")
        logging.info(u"Was initialized procedure set_state.")
        self.zk_conn.ensure_path(children)
        try:
            self.zk_conn.set(children, state)
        except Exception as e:
            self.zk_stop()
            logging.exception(e)
            logging.critical(u"Some error in zk work! Please check zk status.")
            exit(0)
        self.zk_stop()


    def get_state(self, children):
        self.zk_connect("True")
        logging.info(u"Was initialized procedure get_state.")
        try:
            state, data = self.zk_conn.get(children)
        except Exception as e:
            self.zk_stop()
            logging.exception(e)
            logging.critical(u"Some error in zk work! Please check zk status.")
            exit(0)
        self.zk_stop()
        return state, data


    def zk_ensure_path(self, path):
        self.zk_connect("False")
        try:
            result = self.zk_conn.ensure_path(path)
        except Exception as e:
            self.zk_stop()
            logging.exception(e)
            logging.critical(u"Fail to ensure path.")
            exit(0)
        self.zk_stop()
        return result


    def zk_path_exists(self, path):
        self.zk_connect("True")
        try:
            result = self.zk_conn.exists(path)
        except Exception as e:
            self.zk_stop()
            logging.exception(e)
            logging.critical(u"Fail to check exists path.")
            exit(0)
        self.zk_stop()
        return result


    def zk_get_children(self, path):
        self.zk_connect("True")
        try:
            result = self.zk_conn.get_children(path)
        except Exception as e:
            self.zk_stop()
            logging.exception(e)
            logging.critical(u"Fail to get children.")
            exit(0)
        self.zk_stop()
        return result


    def delete_path(self, path):
        self.zk_connect("False")
        try:
            result = self.zk_conn.delete(path, recursive=True)
        except Exception as e:
            self.zk_stop()
            logging.exception(e)
            logging.critical(u"Fail to delete path.")
            exit(0)
        self.zk_stop()
        return result


if __name__ == '__main__':
    # app.run(host='0.0.0.0')
    app.run()


