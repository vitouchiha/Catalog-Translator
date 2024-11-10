var transteArray = [];

async function translateSelected(authKey, selectList) {
    const collection = await stremioAddonCollectionGet(authKey);
    var addons = [];

    
    for(var i=0; i<collection.result.addons.length; i++) {
        addons.push({
            "manifest": collection.result.addons[i].manifest,
            "transportUrl": collection.result.addons[i].transportUrl,
            "flags": {
                "official": false,
                "protected": false
            }
        });
    }

    for(var j=0; j<selectList.length; j++) {
        for(var i=0; i<addons.length; i++) {
            if (selectList[j].id == addons[i].manifest.id) {
                var addonUrl = generateTranslatorLink(addons[i].transportUrl);
                var response = await fetch(addonUrl);
                var tranlatorManifest = await response.json();
                addons[i] = {
                    "manifest": tranlatorManifest,
                    "transportUrl": `${addonUrl}?skip_poster=${selectList[j].skipPoster}`,
                    "flags": {
                        "official": false,
                        "protected": false
                    }
                };
                break;
            }
        }
        // Add new addon
        var addonUrl = generateTranslatorLink(selectList[j].transportUrl);
        var response = await fetch(addonUrl);
        var tranlatorManifest = await response.json();
        addons[i] = {
            "manifest": tranlatorManifest,
            "transportUrl": `${addonUrl}?skip_poster=${selectList[j].skipPoster}`,
            "flags": {
                "official": false,
                "protected": false
            }
        };
    }
    console.log(addons);
    var resp = await stremioAddonCollectionSet(authKey, addons);
    if (resp.result.success == true) {
        alert("Addon installati correttamente!")
        //Refresh addons
        await reloadAddons(authKey);
    }
}

async function reloadAddons(authKey) {
    transteArray = [];
    const addons = document.querySelectorAll(".addon-info");
    addons.forEach(addon => addon.remove());
    await stremioLoadAddons(authKey);
}

function generateTranslatorLink(addonUrl) {
    const serverUrl = window.location.origin;
    addonUrl = removeGetParams(addonUrl);
    if (addonUrl.includes(serverUrl)) {
        return addonUrl;
    }
    const urlEncoded = btoa(addonUrl.replace("/manifest.json", ""));
    const finalUrl = `${serverUrl}/${urlEncoded}/manifest.json`;
    return finalUrl
}

function removeGetParams(url) {
    const urlObj = new URL(url);
    urlObj.search = '';           
    return urlObj.toString();     
}
