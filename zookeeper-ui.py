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
import urllib
from markupsafe import Markup
import random
import os
from kazoo.exceptions import NoAuthError


app = Flask(__name__)
app.secret_key = '[\xaf\xbd\x1dV\xb5#\x80\xff\xa7\x9a1p\xb1\xc4\x99\x07X\xa0\xb9W5\xfdC'


@app.route('/')
def index():
    path = "/"
    znode_stats_list = []
    cluster_available = "True"
    breadcrumb = []
    zk_conf = get_clusters()
    zk_conn = ZkWork().zk_connect(session['readonly'])
    if zk_conn == False:
        cluster_available = "False"
        return render_template("index.html", znodes=[], breadcrumb_list=[], now_path=path,
                           zk_conf=zk_conf, now_cluster=session['cluster'], readonly=session['readonly'],
                           cluster_available=cluster_available, enable_acl=session['enable_acl'])
    root_znodes = ZkWork().zk_get_children(path, zk_conn)
    for i in root_znodes:
        znode_stats = {}
        znode_stats['acl'] = ''
        znode_stats["node"] = i
        data, state, node_acl = ZkWork().get_state(path + "/" + i, zk_conn)
        if data != None:
            znode_stats["data"] = data.decode('utf-8', errors='ignore')
        else:
            znode_stats["data"] = data
        for acl in node_acl:
            znode_stats['acl'] += ("Acl_list - " + str(acl.acl_list) + " for " + str(acl.id)) + "  "
        znode_stats["mtime"] = datetime.datetime.fromtimestamp(state.mtime / 1000).strftime('%Y-%m-%d %H:%M:%S')
        znode_stats["ctime"] = datetime.datetime.fromtimestamp(state.ctime / 1000).strftime('%Y-%m-%d %H:%M:%S')
        znode_stats["cversion"] = state.cversion
        znode_stats["numChildren"] = state.numChildren
        znode_stats_list.append(znode_stats)
    ZkWork().zk_stop(zk_conn)
    return render_template("index.html", znodes=znode_stats_list, breadcrumb_list=breadcrumb, now_path=path,
                           zk_conf=zk_conf, now_cluster=session['cluster'], readonly=session['readonly'],
                           cluster_available=cluster_available, enable_acl=session['enable_acl'])


@app.route('/view/<path:path>')
def next_znode(path):
    logging.info(path)
    session['cluster'] = request.args.get('cluster')
    znode_stats_list = []
    cluster_available = "True"
    breadcrumb_render_list = []
    previous_znode = ''
    breadcrumb = re.split("/", path)
    now_path = "/" + path + "/"
    zk_conf = get_clusters()
    zk_conn = ZkWork().zk_connect(session['readonly'])
    if zk_conn == False:
        cluster_available = "False"
        return render_template("index.html", znodes=[], breadcrumb_list=[], now_path=path,
                           zk_conf=zk_conf, now_cluster=session['cluster'],
                           readonly=session['readonly'], cluster_available=cluster_available, enable_acl=session['enable_acl'])
    znodes = ZkWork().zk_get_children(path, zk_conn)
    for znode in breadcrumb:
        breadcrumb_dict = {}
        breadcrumb_dict["url"] = "/view" + previous_znode + "/" + znode
        breadcrumb_dict["name"] = znode
        breadcrumb_render_list.append(breadcrumb_dict)
        previous_znode += "/" + znode
    for znode in znodes:
        znode_stats = {}
        znode_stats['acl'] = ''
        znode_stats["breadcrumb"] = re.split("/", path)
        znode_stats["node"] = path + "/" + znode
        data, state, node_acl = ZkWork().get_state(path + "/" + znode, zk_conn)
        if data != None:
            znode_stats["data"] = data.decode('utf-8', errors='ignore')
        else:
            znode_stats["data"] = data
        for acl in node_acl:
            znode_stats['acl'] += ("Acl_list - " + str(acl.acl_list) + " for " + str(acl.id)) + "  "
        znode_stats["mtime"] = datetime.datetime.fromtimestamp(state.mtime / 1000).strftime('%Y-%m-%d %H:%M:%S')
        znode_stats["ctime"] = datetime.datetime.fromtimestamp(state.ctime / 1000).strftime('%Y-%m-%d %H:%M:%S')
        znode_stats["cversion"] = state.cversion
        znode_stats["numChildren"] = state.numChildren
        znode_stats_list.append(znode_stats)
    ZkWork().zk_stop(zk_conn)
    return render_template("index.html", znodes=znode_stats_list, breadcrumb_list=breadcrumb_render_list,
                           now_path=now_path, zk_conf=zk_conf, now_cluster=session['cluster'],
                           readonly=session['readonly'], cluster_available=cluster_available, enable_acl=session['enable_acl'])


@app.route('/create', methods=['POST'])
def create():
    try:
        zk_conn = ZkWork().zk_connect(session['readonly'])
        new_znode_name = request.form['new_znode_name']
        new_znode_data = request.form['new_znode_data']
        logging.info(u"Create znode: " + new_znode_name + u" set new data: " + new_znode_data)
        ZkWork().set_state(new_znode_name, str(new_znode_data), zk_conn)
        ZkWork().zk_stop(zk_conn)
    except Exception as e:
        logging.exception(e)
        logging.critical(u"Some problems in create function.")
        try:
            ZkWork().zk_stop(zk_conn)
        except Exception:
            pass
    return json.dumps({'status': 'OK'})


@app.route('/modify', methods=['POST'])
def modify():
    try:
        zk_conn = ZkWork().zk_connect(session['readonly'])
        new_znode_data = request.form['new_znode_data_modify']
        new_znode_path = request.form['node_name']
        logging.info(u"Modify znode: " + new_znode_path + u" set new data: " + new_znode_data)
        ZkWork().set_state(new_znode_path, str(new_znode_data), zk_conn)
        ZkWork().zk_stop(zk_conn)
    except Exception as e:
        logging.exception(e)
        logging.critical(u"Some problems in modify function.")
        try:
            ZkWork().zk_stop(zk_conn)
        except Exception:
            pass
    return json.dumps({'status': 'OK'})


@app.route('/delete', methods=['POST'])
def delete():
    try:
        zk_conn = ZkWork().zk_connect(session['readonly'])
        delete_znode = request.form['delete_znode']
        logging.info(u"Delete node: " + delete_znode)
        ZkWork().delete_path(delete_znode, zk_conn)
        ZkWork().zk_stop(zk_conn)
    except Exception as e:
        logging.exception(e)
        logging.critical(u"Some problems in delete function.")
        try:
            ZkWork().zk_stop(zk_conn)
        except Exception:
            pass
    return json.dumps({'status': 'OK'})


@app.route('/clusters', methods=['POST'])
def clusters():
    session['cluster'] = request.form['cluster']
    return json.dumps({'status': 'OK'})


@app.route('/ping')
def ping():
    return json.dumps({'status': 'OK'})

@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote(s, ":/")
    return Markup(s)


def get_clusters():
    os.chdir(path_to_confdir)
    files = os.listdir(path_to_confdir)
    yaml_configs = filter(lambda x: x.endswith('.yaml'), files)
    zk_conf = {}
    for conf in yaml_configs:
        try:
            with open(conf, "r") as yaml_zk_conf:
                zk_conf.update(yaml.load(yaml_zk_conf))
                yaml_zk_conf.close()
        except IOError as e:
            logging.exception(e)
            exit(0)
    if 'cluster' not in session:
        logging.info(u"Random choise first cluster.")
        session['cluster'] = random.choice(zk_conf.keys())
    if session['cluster'] not in zk_conf.keys():
        logging.info(u"Random choise new cluster.")
        session['cluster'] = random.choice(zk_conf.keys())

    session['readonly'] = zk_conf[session['cluster']]['readonly']
    session['enable_acl'] = zk_conf[session['cluster']]['acl']
    return zk_conf


class ZkWork:
    def zk_connect(self, read_only_zk):
        logging.info(u"Connect to zk cluster. Read-only: " + read_only_zk)
        try:
            zk_conf = get_clusters()
            zk_servers = zk_conf[session['cluster']]['nodes']
            self.zk_conn = KazooClient(hosts=zk_servers, read_only=read_only_zk)
            self.zk_conn.start()
        except Exception as e:
            logging.info(u"Can`t connect to zk cluster: " + zk_conf[session['cluster']]['nodes'])
            logging.exception(e)
            self.zk_stop(self.zk_conn)
            zk_conn = False
            return zk_conn
        return self.zk_conn


    def zk_stop(self, zk_conn):
        logging.info(u"Close connection to zk.")
        zk_conn.stop()
        zk_conn.close()


    def set_state(self, children, data, zk_conn):
        logging.info(u"Was initialized procedure set_state.")
        try:
            zk_conn.ensure_path(children)
            zk_conn.set(children, data)
        except Exception as e:
            self.zk_stop(zk_conn)
            logging.exception(e)
            logging.critical(u"Fail to set state in path: " + children + u" and data: " + data)
            exit(0)


    def get_state(self, children, zk_conn):
        logging.info(u"Was initialized procedure get_state.")
        try:
            state, data = zk_conn.get(children)
            node_acl = ZkAcl().get_acl(children, zk_conn)
        except Exception as e:
            self.zk_stop(zk_conn)
            logging.exception(e)
            logging.critical(u"Fail to get state in path: " + children)
            exit(0)
        return state, data, node_acl


    def zk_get_children(self, path, zk_conn):
        try:
            result = zk_conn.get_children(path)
        except Exception as e:
            self.zk_stop(zk_conn)
            logging.exception(e)
            logging.critical(u"Fail to get children on path: " + path)
            exit(0)
        return result


    def delete_path(self, path, zk_conn):
        try:
            result = zk_conn.delete(path, recursive=True)
        except Exception as e:
            self.zk_stop(zk_conn)
            logging.exception(e)
            logging.critical(u"Fail to delete path: " + path)
            exit(0)
        return result


class ZkAcl:
    def get_acl(selt, children, zk_conn):
        stat_acls = []
        try:
            stat_acls = zk_conn.get_acls(children)
        except NoAuthError:
            pass
        except Exception as e:
            logging.exception(e)
            logging.critical(u"Can`t get acl for " + children)
            exit(0)
        return stat_acls[0]


if __name__ == '__main__':
    main_config_file = '/etc/zookeeper-ui/zookeeper-ui.conf'
    try:
        with open(main_config_file, "r") as main_zk_conf:
            main_config = yaml.load(main_zk_conf)
            main_zk_conf.close()
    except IOError as e:
        print "Cant find config: {0}".format(main_config_file)
        exit(1)
    global path_to_confdir
    path_to_confdir = main_config['conf_dir']
    if main_config['localhost'] == 'True':
        app_host = '127.0.0.1'
    else:
        app_host = '::'
    if main_config['log_file'] == 'None':
        logging.basicConfig(format=u'[%(asctime)s] %(levelname)-8s %(funcName)20s()[LINE:%(lineno)d]# '
                                   u' %(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format=u'[%(asctime)s] %(levelname)-8s %(funcName)20s()[LINE:%(lineno)d]# '
                                   u' %(message)s', level=logging.INFO, filename=main_config['log_file'])
    app.run(host=app_host, port=int(main_config['port']))



