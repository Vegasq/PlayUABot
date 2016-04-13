export container=playuabot
docker build -t $container ~/playuabot/
docker run -d -h $container --name $container $container
