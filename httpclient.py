#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 Abram Hindle, Tom Tran
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib
import platform

def help():
    print "httpclient.py [GET/POST] [URL]\n"

class HTTPRequest(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    
    # Get the hostname and port number from a url 
    def get_host_port(self,url):
        
        # Get the server's hostname and port
        h_p = re.match(r"(.*)\:(\d+)", url)
            
        # If there is a match, that is, there is a port number
        if h_p:
            hostname = h_p.group(1)
            port = int(h_p.group(2))
        else:
            hostname = url
            port = 80
        
        return hostname, port
            
            
    # Create a socket to the Server
    def connect(self, hostname, port):
                        
        # Using sockets
        try:
            # Create an AF_INET, STREAM socket (TCP)
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error,msg:
            print('Failed to create socket. Error code:' + str(msg[0]+', Error message:' + msg[1]))
            sys.exit();
        
        try:
            remote_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            # Could not resolve hostname
            print('Hostname could not be resolved. Exiting')
            sys.exit()

        #Connect to remote server
        sock.connect((remote_ip,port))
                
        return sock


    # Make the client's header
    def make_header(self, url, command, body=None):
        
        # Remove http:// if it is present
        # This httpclient does not work for https://
        if (url[0:7] == 'http://'):
            url = url[7:]
        
        ### In-common headers for GET and POST ###

        # Check for a query string "?"
        if (url.find('?') != -1):
            url_no_query, query = url.split("?", 1)
            query = "?" + query
        else:
            url_no_query = url
            query = ""
            
        # Check for URL's directory "/"
        # NOTE: No error checking for query in URL for POST
            # SKIP: Setup the directory/query string separately for GET and POST
        if (url_no_query.find('/') != -1):
            virt_host, directory  = url_no_query.split("/", 1)
            directory = "/" + directory + query
        else:
            directory = "/" + query
            virt_host = url_no_query
        
        host = virt_host
                    
        # Set http version, user_agent, accept and conn
        http_v = "HTTP/1.1"
        user_agent = "myhttpclient/1.0 " + platform.system() + \
        " " + platform.release() + " " + platform.processor()
        accept = "*/*"
        conn = "close"       
        
        # Add Content headers for POST
        if (command == 'POST' and body != None):
            c_type = "Content-Type: application/x-www-form-urlencoded"
            c_length = "Content-Length: %d" % (len(body))
            
        # Setup full header
        request_line = command + " " + directory + " " + http_v
        user_agent = "User-Agent: " + user_agent
        virt_host = "Host: " + virt_host
        accept = "Accept: " + accept
        conn = "Connection: " + conn
        
        if (command == 'POST' and body != None):
            header = request_line + "\r\n" + user_agent + "\r\n" + virt_host \
            + "\r\n" + c_type + "\r\n"+ c_length + "\r\n" + accept \
            + "\r\n" + conn + "\r\n\r\n"                
        else:
            header = request_line + "\r\n" + user_agent + "\r\n" + virt_host \
            + "\r\n" + accept + "\r\n" + conn + "\r\n\r\n"
        
        return host, header
    
    
    # Get the code of the response
    def get_code(self, data):
        data_parse = re.match(r"(.*) (\d+)", data)
        return int(data_parse.group(2))


    # Get the header of the response    
    def get_headers(self,data):
        
        # The head will be in position 1, 
        data_parse = re.split("\n\n", data, 1)
        if(len(data_parse) >= 2): 
            return data_parse[0]
        return data


    # Get the body of the response 
    def get_body(self, data):
      
        # The body will be in position 2
        data_parse = re.split("\n\n", data, 1)
        if(len(data_parse) >= 2):
            return data_parse[1]
        return ""


    # Read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done: 
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return str(buffer)


    # Perform a GET method to the given URL
    def GET(self, url, args=None):
        
        command = 'GET'
         
        # Setup the body information
        # No body for GET requests
        
        # Setup the header information
        url_modified, myheader = self.make_header(url, command)

        # Get hostname and port
        hostname, port = self.get_host_port(url_modified)
           
        # Connect to the server
        sock = self.connect(hostname, port)
        
        # Send the client message    
        message = myheader
        try:
            # Send the whole string
            sock.sendall(message.encode("UTF8"))
            # Print client's sent message to stdout
            print message
        except socket.error:
            # Send failed
            print('Send failed')
            sys.exit()

        # Receive the response
        data = self.recvall(sock)
        
        # Remove all "\r"
        data = data.replace("\r", "")
        print data
        
        code = self.get_code(data)
        header = self.get_headers(data)
        body = self.get_body(data)

        return HTTPRequest(code, body)         

    # Perform a POST method to the given URL
    def POST(self, url, args=None):
        
        # TEST -- WORKS!
        #url = "http://www.w3schools.com/tags/demo_form_method_post.asp"
        #args = {'fname':'Tom First Name', 'lname':'Tra Last ah'}
        
        command = 'POST'
        
        # Setup the body information
        if (args != None):
            mybody = urllib.urlencode(args) 
    
        # Setup the header information
        if (args != None):
            url_modified, myheader = self.make_header(url, command, mybody)
        else:
            url_modified, myheader = self.make_header(url, command)
        
        # Get hostname and port
        hostname, port = self.get_host_port(url_modified)
           
        # Connect to the server
        sock = self.connect(hostname, port)
        
        # Send the client message
        myheader = myheader.encode("UTF8")        
        if (args != None):
            message = myheader + mybody
        else:
            message = myheader
        try:
            # Send the whole string
            sock.sendall(message)
            # Print client's sent message to stdout
            print message
        except socket.error:
            # Send failed
            print('Send failed')
            sys.exit()

        # Receive the response
        data = self.recvall(sock)
        
        # Remove all "\r"
        data = data.replace("\r", "")        
        print data
        
        code = self.get_code(data)
        header = self.get_headers(data)
        body = self.get_body(data)

        return HTTPRequest(code, body)         
        
        
    # Make the respective call to GET or POST
    def command(self, command, url, args=None):
        
        # Do GET by default if the second input arg is not POST
        if (command == "POST"):
            # return self.POST( url, args )
            return self.POST(url)
        else:
            #return self.GET(url, args)
            return self.GET(url)
    
    
if __name__ == "__main__":
    
    client = HTTPClient()
    if (len(sys.argv) == 3):
        print client.command(sys.argv[1], sys.argv[2])
    else:
        help()
        sys.exit(1)  
        
