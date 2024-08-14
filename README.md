# Cleanup
this is for personal useage , it cleanup my radarr, sonarr media files

# Doc

Dir Check happen in this order

| Env variables              | true                                                                         | false         |
| -------------------------- | ---------------------------------------------------------------------------- | ------------- |
| DELETE_ON_TIME_LIMIT       | Delete if any dir exceeds time limit even if the size limit does not exceeds | Do not delete |
| DELETE_ON_SIZE_LIMIT       | Delete child dirs only if parent dir exceeds size limit                      | Do not delete |
| FORCE_DELETE_ON_SIZE_LIMIT | Delete child dirs if parent dir exceeds size limit or time limit either way  | Do not delete |



Delete if anything exceeds time limit even if size limit doesnt exceeds
So anything older than time limit gets deleted, this can make your dir empty if no new dir added  
```.env
DELETE_ON_TIME_LIMIT=true
DELETE_ON_SIZE_LIMIT=false
FORCE_DELETE_ON_SIZE_LIMIT=false
```

Only Start deleting if size limit of parent dir exceeds,only delete dirs that have exceeded time limit
This way, nothing will be deleted until size limit exceeded
```.env
DELETE_ON_TIME_LIMIT=false
DELETE_ON_SIZE_LIMIT=true
FORCE_DELETE_ON_SIZE_LIMIT=false
```

Delete if size limit of parent dir exceeds and also delete even if dirs doesn't exceeded time limit
So dir the dir never exceeds its size limit
```.env
DELETE_ON_TIME_LIMIT=false
DELETE_ON_SIZE_LIMIT=false
FORCE_DELETE_ON_SIZE_LIMIT=true
```
