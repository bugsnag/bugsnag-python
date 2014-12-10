try:
    import sys; raise Exception("start")
except Exception, e: start_of_file = sys.exc_info()
# 4
# 5
# 6
# 7
# 8
try:
    import sys; raise Exception("end")
except Exception, e: end_of_file = sys.exc_info()
