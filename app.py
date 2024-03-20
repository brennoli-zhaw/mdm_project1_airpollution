link = "https://aqicn.org/station/@57451/de/"
linkParts = link.split("@")
idPart = linkParts[0].split("/")
stationID = idPart[0]
print(stationID)
newLink = "https://airnet.waqi.info/airnet/feed/instant/" + stationID
print(newLink)