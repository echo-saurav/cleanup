# Cleanup
this is for personal useage , it cleanup my radarr, sonarr media files

# Doc

Dir Check happen in this order

| Env variables              | true                                                                         | false         |
| -------------------------- | ---------------------------------------------------------------------------- | ------------- |
| DELETE_ON_TIME_LIMIT       | Delete if any dir exceeds time limit even if the size limit does not exceeds | Do not delete |
| DELETE_ON_SIZE_LIMIT       | Delete child dirs only if parent dir exceeds size limit                      | Do not delete |
| FORCE_DELETE_ON_SIZE_LIMIT | Delete child dirs if parent dir exceeds size limit or time limit either way  | Do not delete |

