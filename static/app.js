// DuitScan App client logic
document.addEventListener("DOMContentLoaded", () => {
    // Canvas contexts
    const latticeCanvas = document.getElementById("lattice-canvas");
    const latticeCtx = latticeCanvas.getContext("2d");
    
    const oscCanvas = document.getElementById("oscilloscope");
    const oscCtx = oscCanvas.getContext("2d");
    
    // UI Elements
    const mStability = document.getElementById("m-stability");
    const mNodes = document.getElementById("m-nodes");
    const mPower = document.getElementById("m-power");
    const mSaving = document.getElementById("m-saving");
    
    const netStatusBadge = document.getElementById("network-status-badge");
    const netStatusText = document.getElementById("network-status-text");
    const latticeEnergyText = document.getElementById("lattice-energy-text");
    
    const blockList = document.getElementById("block-explorer-list");
    const vaultBalances = document.getElementById("vault-balances");
    const l2MempoolList = document.getElementById("l2-mempool-list");
    const botStats = document.getElementById("bot-stats");
    
    const sdkConsole = document.getElementById("sdk-console-log");
    const btnSendTx = document.getElementById("btn-send-tx");
    
    const tempSlider = document.getElementById("temp-slider");
    const tempLabel = document.getElementById("temp-label");
    const btnResetTemp = document.getElementById("btn-reset-temp");
    const btnTriggerFreeze = document.getElementById("btn-trigger-freeze");

    // State Variables
    let selectedWalletMode = "hot";
    let noiseHistory = Array(100).fill(0);
    let sseSource = null;

    // Set canvas sizes for HD display
    function resizeCanvases() {
        // Lattice
        latticeCanvas.width = 400;
        latticeCanvas.height = 400;
        
        // Oscilloscope
        const rect = oscCanvas.parentElement.getBoundingClientRect();
        oscCanvas.width = rect.width;
        oscCanvas.height = 100;
    }
    window.addEventListener("resize", resizeCanvases);
    resizeCanvases();

    // 1. Wallet Selection Mode
    const walletOptions = document.querySelectorAll(".wallet-option");
    walletOptions.forEach(opt => {
        opt.addEventListener("click", () => {
            walletOptions.forEach(o => o.classList.remove("active"));
            opt.classList.add("active");
            selectedWalletMode = opt.dataset.mode;
            
            // Log to simulated client console
            logConsole(`[SDK] Mengalihkan dompet ke mode: ${opt.innerText}`, "info");
            if (selectedWalletMode === "usb") {
                logConsole("[SDK] Menunggu koneksi Hardwallet Dongle USB...", "info");
                setTimeout(() => {
                    logConsole("[SDK] Hardwallet Analog Terhubung (Dongle USB Memristor). Keamanan dijamin Hukum Termodinamika.", "success");
                }, 800);
            } else if (selectedWalletMode === "nfc") {
                logConsole("[SDK] NFC interface aktif. Tempelkan kartu NFC ke smartphone kasir DuitLap.", "info");
            } else {
                logConsole("[SDK] Hot Wallet aktif (Emulasi kalkulasi termal via perangkat lunak).", "info");
            }
        });
    });

    // Console Logging Helper
    function logConsole(message, type = "default") {
        const line = document.createElement("div");
        line.className = `sdk-console-line ${type}`;
        line.innerText = `[${new Date().toLocaleTimeString()}] ${message}`;
        sdkConsole.appendChild(line);
        sdkConsole.scrollTop = sdkConsole.scrollHeight;
    }

    // 2. Oscilloscope Drawing
    function drawOscilloscope() {
        oscCtx.fillStyle = "#020108";
        oscCtx.fillRect(0, 0, oscCanvas.width, oscCanvas.height);
        
        // Grid lines
        oscCtx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        oscCtx.lineWidth = 1;
        oscCtx.beginPath();
        for (let i = 0; i < oscCanvas.width; i += 20) {
            oscCtx.moveTo(i, 0);
            oscCtx.lineTo(i, oscCanvas.height);
        }
        for (let i = 0; i < oscCanvas.height; i += 20) {
            oscCtx.moveTo(0, i);
            oscCtx.lineTo(oscCanvas.width, i);
        }
        oscCtx.stroke();

        // Draw noise trace
        oscCtx.strokeStyle = "rgba(34, 211, 238, 0.85)";
        oscCtx.shadowColor = "rgba(34, 211, 238, 0.5)";
        oscCtx.shadowBlur = 4;
        oscCtx.lineWidth = 1.5;
        oscCtx.beginPath();
        
        const step = oscCanvas.width / (noiseHistory.length - 1);
        for (let i = 0; i < noiseHistory.length; i++) {
            // Map fluctuation voltage to canvas amplitude (-1uV to +1uV mapping)
            const voltage = noiseHistory[i];
            const y = (oscCanvas.height / 2) - (voltage * 5e7); 
            if (i === 0) {
                oscCtx.moveTo(0, y);
            } else {
                oscCtx.lineTo(i * step, y);
            }
        }
        oscCtx.stroke();
        
        // Reset shadows
        oscCtx.shadowBlur = 0;
        requestAnimationFrame(drawOscilloscope);
    }
    requestAnimationFrame(drawOscilloscope);

    // 3. Lattice Ising Model Drawing
    function drawLattice(grid) {
        latticeCtx.fillStyle = "#06050c";
        latticeCtx.fillRect(0, 0, latticeCanvas.width, latticeCanvas.height);

        const rows = grid.length;
        const cols = grid[0].length;
        const cellSize = latticeCanvas.width / cols;
        const radius = (cellSize / 2) * 0.75;

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const val = grid[r][c];
                const cx = c * cellSize + cellSize / 2;
                const cy = r * cellSize + cellSize / 2;

                latticeCtx.beginPath();
                latticeCtx.arc(cx, cy, radius, 0, 2 * Math.PI);
                
                // Color mapping: +1 is Purple (Spin Up), -1 is Cyan (Spin Down)
                if (val === 1) {
                    latticeCtx.fillStyle = "#c084fc";
                    latticeCtx.shadowColor = "rgba(192, 132, 252, 0.8)";
                    latticeCtx.shadowBlur = 8;
                } else {
                    latticeCtx.fillStyle = "#22d3ee";
                    latticeCtx.shadowColor = "rgba(34, 211, 238, 0.8)";
                    latticeCtx.shadowBlur = 8;
                }
                
                latticeCtx.fill();
            }
        }
        latticeCtx.shadowBlur = 0; // reset
    }

    // 4. SSE Stream Telemetry listener
    function startSSE() {
        if (sseSource) {
            sseSource.close();
        }
        
        sseSource = new EventSource("/api/v1/network/stream");
        
        sseSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Push noise
            noiseHistory.push(data.voltage);
            noiseHistory.shift();

            // Draw Lattice Grid
            drawLattice(data.lattice);
            
            // Update labels
            mStability.innerText = `${data.stability}%`;
            mStability.className = data.stability > 80 ? "metric-card-value highlight-cyan" : "metric-card-value highlight-purple";
            
            latticeEnergyText.innerText = `System Hamiltonian: H = ${data.energy}`;
            
            // Network Status Badge
            if (data.safe_mode_active) {
                netStatusBadge.className = "status-badge frozen";
                netStatusText.innerText = "COOLING-OFF (FROZEN)";
                mNodes.innerText = "12 (Failsafe)";
                mPower.innerText = "12.4 Watts";
            } else {
                netStatusBadge.className = "status-badge";
                netStatusText.innerText = "THERMAL RUNNING";
                mNodes.innerText = "4209";
                
                // Calculate dynamic wattage
                const watts = 800.0 + (100.0 - data.stability) * 4.2;
                mPower.innerText = `${watts.toFixed(1)} Watts`;
            }
            
            // Live energy saving metric
            const baseSave = 14.242;
            const diffTime = (Date.now() / 1000) % 1000;
            mSaving.innerText = `${(baseSave + diffTime * 0.005).toFixed(3)} MWh`;

            // Update Burned Supply Badge
            if (data.balances) {
                const burnedVal = data.balances["0x000000000000000000000000000000000000DEAD"] || 0.0;
                const burnedEl = document.getElementById("burned-supply-badge");
                if (burnedEl) {
                    burnedEl.innerText = `${burnedVal.toLocaleString()} $DUIT`;
                }
            }

            // L1 Blocks Update
            renderBlocks(data.blocks);

            // Balances Update
            renderBalances(data.balances);

            // L2 Mempool Update
            renderMempool(data.l2_pool);

            // Bots Update
            renderBots(data.bots);
        };
        
        sseSource.onerror = (err) => {
            console.error("SSE Connection error", err);
            sseSource.close();
            // Retry in 3 seconds
            setTimeout(startSSE, 3000);
        };
    }
    startSSE();

    // Render blocks list
    function renderBlocks(blocks) {
        if (!blocks) return;
        blockList.innerHTML = "";
        
        // Reverse order so newest blocks appear first
        const sorted = [...blocks].reverse();
        sorted.forEach(block => {
            const card = document.createElement("div");
            card.className = "block-card";
            
            const timeStr = new Date(block.timestamp * 1000).toLocaleTimeString();
            const txCount = block.transactions ? block.transactions.length : 0;
            const winningBot = block.winning_bot ? block.winning_bot : "Organic Cycle";
            const botSaving = block.bot_saving_pct ? `${block.bot_saving_pct}% Saved` : "N/A";
            
            card.innerHTML = `
                <div class="block-card-header">
                    <span class="block-height">BLOCK #${block.block_height}</span>
                    <span class="block-time">${timeStr}</span>
                </div>
                <div class="block-details">
                    <div class="block-detail-item">Thermic state: <span>${block.lattice_energy_state}</span></div>
                    <div class="block-detail-item">Entropy &Delta;S: <span>${block.delta_entropy}</span></div>
                    <div class="block-detail-item">Transactions: <span>${txCount}</span></div>
                    <div class="block-detail-item">Harvester: <span>${winningBot}</span></div>
                </div>
                <div class="block-hash">Entropy Hash: ${block.settled_entropy}</div>
            `;
            blockList.appendChild(card);
        });
    }

    // Render accounts
    function renderBalances(balances) {
        if (!balances) return;
        vaultBalances.innerHTML = "";
        
        // Label mapping
        const names = {
            "0x01a2b3": "Treasury Bridge L1",
            "0x02bf1a": "DuitLap Cashier Merchant",
            "0x03a6bc": "Consumer Wallet",
            "0xBotHarvester": "Arbitrage Bots Pool",
            "0x000000000000000000000000000000000000DEAD": "Absolute Heat Sink (Burned)"
        };
        
        for (const [addr, bal] of Object.entries(balances)) {
            const row = document.createElement("div");
            row.className = "balance-row";
            
            const displayName = names[addr] || `Node Validator (${addr.substring(0,8)})`;
            
            row.innerHTML = `
                <span class="balance-addr" style="color: var(--text-muted);">${displayName}</span>
                <span class="balance-val" style="font-weight: bold; color: var(--secondary);">${bal.toLocaleString()} $DUIT</span>
            `;
            vaultBalances.appendChild(row);
        }
    }

    // Render Mempool (L2 pond)
    function renderMempool(pool) {
        if (!pool || pool.length === 0) {
            l2MempoolList.innerHTML = `<div class="l2-empty">Pond is dry. Send payments to stress-field coordinates.</div>`;
            return;
        }
        
        l2MempoolList.innerHTML = "";
        pool.forEach(tx => {
            const item = document.createElement("div");
            item.className = "l2-pond-item";
            
            const amountDuit = tx.amount_joules / 1e8;
            item.innerHTML = `
                <div>
                    <span style="color:#fff; font-weight:bold;">${tx.sender.substring(0,6)}...</span>
                    <span>&rarr;</span>
                    <span style="color:#fff; font-weight:bold;">${tx.recipient.substring(0,6)}...</span>
                </div>
                <div style="color: var(--primary); font-weight:bold;">
                    ${amountDuit.toFixed(2)} $DUIT
                </div>
            `;
            l2MempoolList.appendChild(item);
        });
    }

    // Render Bots
    function renderBots(bots) {
        if (!bots) return;
        botStats.innerHTML = "";
        
        bots.forEach(bot => {
            const row = document.createElement("div");
            row.className = "bot-row";
            
            row.innerHTML = `
                <span class="bot-name">${bot.id}</span>
                <span style="font-size: 10px; color: var(--text-muted);">Eff: ${(bot.efficiency_score*100).toFixed(0)}%</span>
                <span class="bot-wins" style="color: var(--green-glow);">${bot.wins} wins</span>
            `;
            botStats.appendChild(row);
        });
    }

    // 5. Send Transaction Client SDK Flow
    btnSendTx.addEventListener("click", async () => {
        const recipient = document.getElementById("tx-recipient").value;
        const amountDuit = parseFloat(document.getElementById("tx-amount").value);
        
        if (!recipient || isNaN(amountDuit) || amountDuit <= 0) {
            logConsole("Error: Invalid recipient address or amount.", "error");
            return;
        }
        
        // Convert to Joule
        const amountJoule = Math.round(amountDuit * 1e8);
        const sender = "0x03a6bc"; // Consumer Wallet
        
        logConsole("[SDK SDK] Executing DuitWallet.sendMicroTransaction()...", "info");
        
        try {
            // STEP 1: PREPARE TRANSACTION
            logConsole(`[SDK] Step 1: Requesting prepare for ${amountDuit} DUIT (${amountJoule} Joules)...`, "info");
            const prepResponse = await fetch("/api/v1/transaction/prepare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    sender_public_key: sender,
                    recipient: recipient,
                    amount_joule: amountJoule
                })
            });
            
            if (!prepResponse.ok) {
                const errData = await prepResponse.json();
                throw new Error(errData.detail || "Failed to prepare transaction");
            }
            
            const prepData = await prepResponse.json();
            logConsole(`[SDK] Target energy state resolved to: ${prepData.target_energy_state}`, "info");
            logConsole(`[SDK] Entropy Jendela Noise salt captured: ${prepData.entropy_salt.substring(0,12)}...`, "info");
            
            // STEP 2: OTENTIKASI BIOMETRIC ENTROPY
            logConsole("[SDK] Step 2: Requesting User Biometric Entropy authentication...", "info");
            // Simulate reading local device thermal noise signature + user biometrics
            await new Promise(resolve => setTimeout(resolve, 600)); // user scan delay
            logConsole("[SDK] Biometric entropy signature generated. State Energy Proof finalized.", "success");
            
            // STEP 3: COMMIT TRANSACTION
            logConsole("[SDK] Step 3: Sending energy proof back to validator API...", "info");
            const commitResponse = await fetch("/api/v1/transaction/commit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    signed_energy_proof: "0x8a7b6c" + Math.random().toString(16).slice(2, 8),
                    transaction_payload: {
                        sender_public_key: sender,
                        recipient: recipient,
                        amount_joule: amountJoule,
                        entropy_salt: prepData.entropy_salt,
                        target_energy_state: prepData.target_energy_state
                    }
                })
            });
            
            if (!commitResponse.ok) {
                const errData = await commitResponse.json();
                throw new Error(errData.detail || "Failed to commit transaction");
            }
            
            const commitData = await commitResponse.json();
            logConsole(`[SDK] Transaksi Kasir Sukses! Terkunci di Blok L1: #${commitData.block_height}`, "success");
            logConsole(`[SDK] Tx L2 ID: ${commitData.tx_id}`, "success");
            
        } catch (e) {
            logConsole(`[SDK] Error: Gagal mencapai kesetimbangan energi transaksi: ${e.message}`, "error");
        }
    });

    // 6. Perturbation Control Slider Updates
    tempSlider.addEventListener("input", async () => {
        const level = parseFloat(tempSlider.value);
        tempLabel.innerText = `${level.toFixed(2)} \u00B0C`;
        
        await fetch("/api/v1/network/disturbance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ level: level })
        });
    });

    btnResetTemp.addEventListener("click", async () => {
        tempSlider.value = 0;
        tempLabel.innerText = "0.00 \u00B0C";
        
        await fetch("/api/v1/network/disturbance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ level: 0.0 })
        });
        logConsole("[SDK] Lattice temperature reset. Nodes returning to normal state.", "info");
    });

    btnTriggerFreeze.addEventListener("click", async () => {
        tempSlider.value = 5.5;
        tempLabel.innerText = "5.50 \u00B0C";
        
        await fetch("/api/v1/network/disturbance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ level: 5.5 })
        });
        logConsole("[SDK] WARNING: Thermal instability injected. Network entered safe mode cooling-off freeze.", "error");
    });

    // 7. Thermoscan Search Engine Integration
    const searchInput = document.getElementById("thermoscan-search");
    const searchTrigger = document.getElementById("btn-search-trigger");
    const searchModal = document.getElementById("search-modal");
    const searchModalTitle = document.getElementById("search-modal-title");
    const searchModalBody = document.getElementById("search-modal-body");
    const btnModalClose = document.getElementById("btn-modal-close");

    async function executeSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        searchModalTitle.innerText = "SEARCHING...";
        searchModalBody.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--secondary);">Mencari data termodinamika di SQLite...</div>`;
        searchModal.classList.add("active");

        try {
            const response = await fetch(`/api/v1/search?query=${encodeURIComponent(query)}`);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error("Data tidak ditemukan. Silakan cek kembali tinggi blok, hash, atau alamat.");
                }
                throw new Error("Terjadi kesalahan koneksi server.");
            }

            const result = await response.json();
            searchModalTitle.innerText = `RESULT FOUND: ${result.type.toUpperCase()}`;

            if (result.type === "block") {
                const b = result.data;
                const timeStr = new Date(b.timestamp * 1000).toLocaleString();
                const txCount = b.transactions ? b.transactions.length : 0;
                searchModalBody.innerHTML = `
<h3 style="color:#fff;">Block Height #${b.block_height}</h3>
<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.05);">
<div>Timestamp: <strong>${timeStr}</strong></div>
<div>Lattice Energy State: <strong>${b.lattice_energy_state}</strong></div>
<div>Entropy Stability (&Delta;S): <strong>${b.delta_entropy}</strong></div>
<div>Validator: <strong>${b.validator}</strong></div>
<div>Winning Bot Optimizer: <strong>${b.winning_bot || 'Organic / None'}</strong></div>
<div>Arbitrage Savings: <strong>${b.bot_saving_pct || 0}%</strong></div>
<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.05);">
<h4 style="color:#fff; margin-bottom:8px;">Transactions inside block (${txCount}):</h4>
${txCount === 0 ? '<em>Tidak ada transaksi di dalam blok ini.</em>' : b.transactions.map((tx, idx) => `
<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 8px; border-radius: 6px; margin-top: 8px;">
  <strong>Tx #${idx + 1} ID:</strong> ${tx.tx_id}<br>
  <strong>Pengirim:</strong> ${tx.sender}<br>
  <strong>Penerima:</strong> ${tx.recipient}<br>
  <strong>Jumlah:</strong> ${(tx.amount_joules / 1e8).toLocaleString()} $DUIT (${tx.amount_joules.toLocaleString()} Joule)
</div>
`).join('')}
                `;
            } else if (result.type === "transaction") {
                const tx = result.data;
                const timeStr = new Date(tx.timestamp * 1000).toLocaleString();
                searchModalBody.innerHTML = `
<h3 style="color:#fff;">Transaction details</h3>
<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.05);">
<div>Transaction ID: <strong>${tx.tx_id}</strong></div>
<div>Block Height: <strong>#${tx.block_height}</strong></div>
<div>Sender Wallet: <strong>${tx.sender}</strong></div>
<div>Recipient Wallet: <strong>${tx.recipient}</strong></div>
<div>Amount: <strong>${(tx.amount_joules / 1e8).toLocaleString()} $DUIT</strong> (${tx.amount_joules.toLocaleString()} Joules)</div>
<div>Entropy Salt: <strong>${tx.entropy_salt}</strong></div>
<div>Target Energy State: <strong>${tx.target_energy_state}</strong></div>
<div>Timestamp: <strong>${timeStr}</strong></div>
                `;
            } else if (result.type === "address") {
                const addr = result.data.address;
                const txs = result.data.transactions;
                searchModalBody.innerHTML = `
<h3 style="color:#fff;">Address Details</h3>
<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.05);">
<div style="word-break: break-all;">Public Address: <strong>${addr}</strong></div>
<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.05);">
<h4 style="color:#fff;">Transaction History (${txs.length}):</h4>
${txs.length === 0 ? '<em>Alamat ini belum memiliki riwayat transaksi di sirkuit SQLite.</em>' : txs.map((tx, idx) => {
    const isSender = tx.sender.toLowerCase() === addr.toLowerCase();
    const prefix = isSender ? "-" : "+";
    const color = isSender ? "var(--accent)" : "var(--green-glow)";
    return `
<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 8px; border-radius: 6px; margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
  <div>
    <strong>Block #${tx.block_height}</strong> &bull; <span style="font-size:10px; color:var(--text-muted);">${new Date(tx.timestamp * 1000).toLocaleTimeString()}</span><br>
    <span style="font-size:10px; color:var(--text-muted);">${isSender ? 'To: ' + tx.recipient.substring(0,8) + '...' : 'From: ' + tx.sender.substring(0,8) + '...'}</span>
  </div>
  <div style="color: ${color}; font-weight: bold; font-family: var(--font-display);">
    ${prefix} ${(tx.amount_joules / 1e8).toLocaleString()} $DUIT
  </div>
</div>
    `;
}).join('')}
                `;
            }
        } catch (err) {
            searchModalTitle.innerText = "ERROR";
            searchModalBody.innerHTML = `<div style="color: var(--accent); font-weight: bold;">${err.message}</div>`;
        }
    }

    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            executeSearch();
        }
    });

    searchTrigger.addEventListener("click", executeSearch);

    btnModalClose.addEventListener("click", () => {
        searchModal.classList.remove("active");
    });

    // 8. Testnet Faucet Integration
    const btnRequestFaucet = document.getElementById("btn-request-faucet");
    const faucetRecipient = document.getElementById("faucet-recipient");

    if (btnRequestFaucet) {
        btnRequestFaucet.addEventListener("click", async () => {
            const recipient = faucetRecipient.value.trim();
            if (!recipient) {
                logConsole("[SDK] Faucet Error: Recipient address cannot be empty.", "error");
                return;
            }

            btnRequestFaucet.disabled = true;
            btnRequestFaucet.innerText = "Requesting...";

            try {
                const response = await fetch("/api/v1/faucet", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ recipient: recipient })
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Failed to call faucet API");
                }

                const result = await response.json();
                logConsole(`[SDK] Faucet Success! 10 $DUIT dispatched to L2. Tx: ${result.tx_id}`, "info");
            } catch (err) {
                logConsole(`[SDK] Faucet Failed: ${err.message}`, "error");
            } finally {
                btnRequestFaucet.disabled = false;
                btnRequestFaucet.innerText = "Minta Saldo Gratis (10 $DUIT)";
            }
        });
    }

    window.addEventListener("click", (e) => {
        if (e.target === searchModal) {
            searchModal.classList.remove("active");
        }
    });
});
