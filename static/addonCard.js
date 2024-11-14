const addonBlackList = [
    "org.stremio.mammamia",                 // Mamma Mia
    "com.linvo.stremiochannels",            // Youtube
    "org.community.orion",                  // Orion
    "stremio.addons.mediafusion|elfhosted", // MediaFusion Elfhosted
    "org.stremio.thepiratebay-catalog",     // TPB Catalog
    "org.zoropogaddon",                     // One Piece Catalog
    "com.noone.stremio-trakt-up-next",      // Trakt Up Next
    "community.usatv",                      // USA TV
    "community.argentinatv",                // Argentina TV
    "tmdb-addon",                           // TMDB Addon
    "pw.ers.concerts"                       // Music Concerts
]


async function loadAddon(url, showError=false) {
    if (!url) {
        alert("Invalid URL.");
        return;
    }

    try {
        const response = await fetch(url);
        if (response.ok) {
            const manifest = await response.json();
            if (!addonBlackList.includes(manifest.id) && "catalogs" in manifest && manifest.catalogs.length > 0) {
                createAddonCard(manifest, url);
            } else {
                if (showError) {
                    alert("Addon non compatibile.");
                }
            }
        } else {
            if (showError){
                alert(`Error: ${response.status}`);
            }
        }

    } catch (error) {
        console.log(error);
    }
}

function createAddonCard(manifest, url) {
    const container = document.getElementById("addons-container");

    const addonCard = document.createElement("div");
    addonCard.className = "addon-info";

    addonCard.appendChild(createAddonHeader(manifest));
    addonCard.appendChild(createAddonDescription(manifest));
    addonCard.appendChild(createAddonVersion(manifest));
    addonCard.appendChild(createSkipPosterOption(manifest));

    const actionsDiv = document.createElement("div");
    actionsDiv.className = "addon-actions";
    const installBtn = createInstallButton(manifest, url);
    actionsDiv.appendChild(installBtn);

    addonCard.appendChild(actionsDiv);
    container.appendChild(addonCard);
}

function createAddonHeader(manifest) {
    const addonHeader = document.createElement("div");
    addonHeader.className = "addon-header";

    const logo = document.createElement("img");
    logo.className = "addon-logo";
    logo.src = manifest.logo || "https://via.placeholder.com/60";
    logo.alt = "Logo dell'addon";
    addonHeader.appendChild(logo);

    const title = document.createElement("h3");
    title.innerText = manifest.name || "N/A";
    addonHeader.appendChild(title);

    return addonHeader;
}

function createAddonDescription(manifest) {
    const description = document.createElement("p");
    description.innerHTML = `<strong>Descrizione:</strong> ${manifest.description || "N/A"}`;
    return description;
}

function createAddonVersion(manifest) {
    const version = document.createElement("p");
    version.innerHTML = `<strong>Versione:</strong> ${manifest.version || "N/A"}`;
    return version;
}

function createSkipPosterOption(manifest) {
    const skipPosterDiv = document.createElement("div");
    skipPosterDiv.className = "skip-poster";

    const skipPosterCheckbox = document.createElement("input");
    skipPosterCheckbox.type = "checkbox";
    skipPosterCheckbox.id = `skipPoster-${manifest.name}`;
    skipPosterDiv.appendChild(skipPosterCheckbox);

    const skipPosterLabel = document.createElement("label");
    skipPosterLabel.htmlFor = `skipPoster-${manifest.name}`;
    skipPosterLabel.innerText = "Skip Poster";
    skipPosterDiv.appendChild(skipPosterLabel);

    return skipPosterDiv;
}

function createInstallButton(manifest, url) {
    const installBtn = document.createElement("button");
    installBtn.className = "install-btn";
    installBtn.innerText = "Seleziona";
    installBtn.state = "active";
    installBtn.onclick = () => toggleAddonSelection(installBtn, manifest, url);
    return installBtn;
}

function toggleAddonSelection(installBtn, manifest, url) {
    const checkbox = document.getElementById(`skipPoster-${manifest.name}`);
    if (installBtn.state === "active") {
        installBtn.state = "not_active";
        installBtn.innerText = "Rimuovi";
        installBtn.style.backgroundColor = "#ff4b4b";
        
        const skipQuery = checkbox.checked ? 1 : 0;
        checkbox.disabled = true;
        manifest.transportUrl = url;
        manifest.skipPoster = skipQuery;
        transteArray.push(manifest);
    } else {
        checkbox.disabled = false;
        installBtn.state = "active";
        installBtn.innerText = "Seleziona";
        installBtn.style.backgroundColor = "#2ecc71";
        
        transteArray = transteArray.filter(item => item !== manifest);
    }
}
