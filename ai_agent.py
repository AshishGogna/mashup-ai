import clipper
import finder
import json
import time

def find(query, page):
    result = finder.get_next_result(query, page)
    return result

def generate_clip(id, link, start, end):
    return clipper.generate_clip(id,link, start, end)