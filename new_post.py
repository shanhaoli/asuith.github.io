# author: suith
# require: python3
# usage:
#       python new_post.py "this is post title"

import sys
from time import localtime
import shutil

post_template = """
---
layout: article
date: "{date} {time} +0800"
title: ""
description: ""
keywords: ""
categories: cs, life 
key: {title}
---

> {{ page.description }}

<!--more-->

"""

file_name_template = "{date}-{title}.md"

if __name__ == '__main__':
    # preapare
    assert len(sys.argv) >= 2
    t = localtime()
    date = "{}-{:0>2}-{:0>2}".format(t.tm_year, t.tm_mon, t.tm_mday)
    time = "{}:{}:{}".format(t.tm_hour, t.tm_hour, t.tm_min)
    title = sys.argv[1] # example 'this is the title'
    titleWithDash = "-".join(title.split())
    
    post = post_template.format(date=date, time=time, title=titleWithDash)
    file_name = file_name_template.format(date=date, title=titleWithDash)
    # print(post)
    # print(file_name)

    # write it down
    with open (file_name, "w") as f:
        f.write(post)
        print("posts {} created.".format(file_name))
    try:
        result = shutil.move(file_name, "_posts")
        print("moved to " + result)
    except:
        print("no _posts folder!")

