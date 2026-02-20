#!/bin/bash
# Archive Adam GEN1
mkdir -p /home/ijneb/digiquarium/archives/adam-gen1
cp -r /home/ijneb/digiquarium/logs/tank-01-adam /home/ijneb/digiquarium/archives/adam-gen1/
docker logs tank-01-adam > /home/ijneb/digiquarium/archives/adam-gen1/full_container_log.txt 2>&1
echo "GEN1 Archived: $(date)" > /home/ijneb/digiquarium/archives/adam-gen1/ARCHIVE_INFO.txt
echo "Articles visited: 44" >> /home/ijneb/digiquarium/archives/adam-gen1/ARCHIVE_INFO.txt
echo "Unique articles: 41" >> /home/ijneb/digiquarium/archives/adam-gen1/ARCHIVE_INFO.txt
echo "Thoughts captured: 39" >> /home/ijneb/digiquarium/archives/adam-gen1/ARCHIVE_INFO.txt
echo "Journey: World War I -> Judaism exploration" >> /home/ijneb/digiquarium/archives/adam-gen1/ARCHIVE_INFO.txt
echo "Done!"
