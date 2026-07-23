import asyncio
import json
import time
import os
from typing import Dict, Any
from contextlib import asynccontextmanager

# Load environment variables from .env file if it exists
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, val = line.strip().split("=", 1)
                os.environ[key.strip()] = val.strip()

# Check for Google Generative AI support
GEMINI_SUPPORTED = False
try:
    from google import genai
    GEMINI_SUPPORTED = True
except ImportError:
    pass
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse

from engine.noise import thermal_noise
from engine.consensus import consensus_lattice
from engine.blockchain import thermo_blockchain
from engine.db import get_block_by_height, get_block_by_hash, get_transaction_by_id, get_transactions_by_address

# Active node count tracker (dynamic simulation)
ACTIVE_NODES = 4209

# Background block commit task
async def block_committer_loop():
    """Simulates the L1 block commit cycle (ticks every 10 seconds)"""
    while True:
        try:
            await asyncio.sleep(10.0)
            if not consensus_lattice.safe_mode_active:
                # Even if the L2 pool is empty, thermodynamic cycles trigger block creation (heartbeat)
                # to maintain network entropy synchronization.
                thermo_blockchain.commit_block()
        except Exception as e:
            print(f"Error in block committer loop: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start block committer background task
    task = asyncio.create_task(block_committer_loop())
    yield
    # Clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Project Renungan Thermodynamic Blockchain Core API", lifespan=lifespan, docs_url="/api/docs")

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/account/{address}/balance")
async def get_account_balance(address: str):
    """Query the current balance of a specific address in Joules and DUIT"""
    balance_joules = thermo_blockchain.accounts.get(address, 0)
    return {
        "address": address,
        "balance_joules": balance_joules,
        "balance_duit": balance_joules / 1e8
    }

@app.post("/api/v1/transaction/prepare")
async def prepare_transaction(data: Dict[str, Any]):
    """
    Step 1: Capture recent entropy state and target physical energy thresholds.
    """
    sender = data.get("sender_public_key")
    recipient = data.get("recipient")
    amount = data.get("amount_joule")

    if not sender or not recipient or amount is None:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive Joules")

    try:
        prep = thermo_blockchain.prepare_transaction(sender, recipient, amount)
        return {
            "status": "prepared",
            "entropy_salt": prep["entropy_salt"],
            "target_energy_state": prep["target_energy_state"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/transaction/commit")
async def commit_transaction(data: Dict[str, Any]):
    """
    Step 2: Commit physical proof of state energy balance to the network.
    """
    signed_energy_proof = data.get("signed_energy_proof")
    payload = data.get("transaction_payload") # Expects dict with sender, recipient, amount_joule, target_energy_state

    if not signed_energy_proof or not payload:
        raise HTTPException(status_code=400, detail="Missing signatures or transaction payload")

    # Reconstruct the target energy state to verify the State Energy Proof
    target_hex = payload.get("target_energy_state")
    if not target_hex:
        raise HTTPException(status_code=400, detail="Invalid payload target energy state")
    
    try:
        # Convert hex target back to floats for physics engine validation
        # (simulating ADC convertor on chip reading memristor state)
        target_energy = float(int(target_hex, 16) & 0xffffff) / 100.0 - 300.0
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed target energy state format")

    # Evaluate the Proof (SEP consensus check)
    is_valid = consensus_lattice.evaluate_state_energy_proof(target_energy)
    if not is_valid:
        raise HTTPException(status_code=400, detail="State Energy Proof mismatch: Failed to achieve equilibrium")

    try:
        tx_id = thermo_blockchain.add_to_l2_pool({
            "sender": payload["sender_public_key"],
            "recipient": payload["recipient"],
            "amount_joules": payload["amount_joule"],
            "entropy_salt": payload["entropy_salt"],
            "target_energy_state": target_hex
        })
        
        # Calculate block height prediction
        block_height = len(thermo_blockchain.chain)
        settled_entropy_mock = thermal_noise.generate_entropy_salt(16)
        
        return {
            "status": "committed",
            "tx_id": tx_id,
            "block_height": block_height,
            "settled_entropy": settled_entropy_mock
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/network/entropy-health")
async def get_entropy_health():
    """
    Returns live metrics on physical performance of the node network.
    """
    stability = consensus_lattice.get_entropy_stability()
    watts = 800.0 + (100.0 - stability) * 4.2 if not consensus_lattice.safe_mode_active else 12.4
    
    # Calculate energy saved vs EVM (mock cumulative metrics scaled by node count)
    energy_saved_mwh = 14.2 + (time.time() % 1000) * 0.005

    return {
        "global_entropy_stability": f"{stability:.2f}%",
        "active_analog_nodes": ACTIVE_NODES if not consensus_lattice.safe_mode_active else 12,
        "global_power_draw_watts": round(watts, 1),
        "energy_saved_vs_evm_mwh": round(energy_saved_mwh, 3),
        "safe_mode_active": consensus_lattice.safe_mode_active
    }

@app.post("/api/v1/network/disturbance")
async def inject_disturbance(data: Dict[str, Any]):
    """
    Simulates physical perturbations (e.g. heating, line drops, noise surges)
    to demonstrate self-healing cooling-off limits.
    """
    level = data.get("level", 0.0)
    consensus_lattice.set_network_disturbance(level)
    return {
        "status": "disturbance_adjusted",
        "current_temperature": round(consensus_lattice.temperature, 4),
        "safe_mode_active": consensus_lattice.safe_mode_active
    }

@app.get("/api/v1/network/stream")
async def event_stream(request: Request):
    """
    SSE stream providing high-frequency physics telemetry updates
    directly to the frontend dashboard.
    """
    async def event_generator():
        while True:
            # Client disconnected?
            if await request.is_disconnected():
                break

            # Let the spin lattice evolve naturally via random thermal walks
            if not consensus_lattice.safe_mode_active:
                consensus_lattice.step_metropolis()

            # Compile status payload
            payload = {
                "lattice": consensus_lattice.grid.tolist(),
                "temperature": round(consensus_lattice.temperature, 3),
                "energy": round(consensus_lattice.get_energy(), 3),
                "magnetization": round(consensus_lattice.get_magnetization(), 3),
                "stability": round(consensus_lattice.get_entropy_stability(), 2),
                "safe_mode_active": consensus_lattice.safe_mode_active,
                "voltage": thermal_noise.read_voltage_fluctuation(),
                "l2_pool": thermo_blockchain.l2_pool,
                # Show last 5 blocks to avoid massive JSON payloads
                "blocks": thermo_blockchain.chain[-5:],
                "balances": {k: round(v / 1e8, 4) for k, v in thermo_blockchain.accounts.items()},
                "bots": thermo_blockchain.bots
            }
            
            yield {
                "event": "message",
                "id": str(int(time.time() * 1000)),
                "retry": 1000,
                "data": json.dumps(payload)
            }
            
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())

@app.get("/api/v1/search")
async def search_ledger(query: str):
    q = query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # 1. Check if query is a block height (integer)
    try:
        height = int(q)
        block = get_block_by_height(height)
        if block:
            return {"type": "block", "data": block}
    except ValueError:
        pass

    # 2. Check if it matches a transaction ID
    tx = get_transaction_by_id(q)
    if tx:
        return {"type": "transaction", "data": tx}
        
    # 3. Check if it matches a block settled entropy hash
    block = get_block_by_hash(q)
    if block:
        return {"type": "block", "data": block}
        
    # 4. Check if it matches an address
    if q.startswith("0x"):
        txs = get_transactions_by_address(q)
        return {"type": "address", "data": {"address": q, "transactions": txs}}
        
    raise HTTPException(status_code=404, detail="No matches found for the query.")

@app.post("/api/v1/faucet")
async def request_faucet(data: Dict[str, Any]):
    recipient = data.get("recipient", "").strip()
    if not recipient or not recipient.startswith("0x"):
        raise HTTPException(status_code=400, detail="Invalid address format. Address must start with '0x'.")
    try:
        result = thermo_blockchain.request_faucet_tokens(recipient)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/chat")
async def chat_assistant(data: Dict[str, Any]):
    message = data.get("message", "").strip()
    if not message:
        return {"reply": "Halo! Silakan masukkan pertanyaan seputar Thermoledger."}
        
    api_key = os.environ.get("GEMINI_API_KEY", "")
    has_real_key = api_key and not api_key.startswith("YOUR_")
    
    if GEMINI_SUPPORTED and has_real_key:
        try:
            client = genai.Client(api_key=api_key)
            system_prompt = (
                "You are Thermoledger AI, a helpful Web3 developer assistant specialized in the Thermoledger protocol. "
                "Thermoledger is a thermodynamic physics-as-computation blockchain. "
                "It uses the Least Action Principle for L2 transaction compression, and State Energy Proof (SEP) based on the 2D Ising Lattice model for L1 consensus. "
                "The L2 token standard is TTS-20 (Thermoledger Token Standard). "
                "Provide clear, concise answers in Indonesian. When displaying code, use python formatting. "
                "Be dynamic and friendly."
            )
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=f"{system_prompt}\n\nUser Query: {message}"
            )
            return {"reply": response.text}
        except Exception as e:
            # Fallback to keyword matcher on exception
            pass

    # Fallback keyword matcher
    message_lower = message.lower()
    if "token" in message_lower or "tts-20" in message_lower or "tts20" in message_lower:
        reply = (
            "Untuk membuat token TTS-20 di Thermoledger L2, Anda dapat menggunakan skrip berikut:\n\n"
            "```python\n"
            "token = ThermoledgerToken(\n"
            "    name=\"NamaToken\",\n"
            "    symbol=\"SYM\",\n"
            "    decimals=8,\n"
            "    initial_supply=10000000\n"
            ")\n"
            "token.set_mintable(False)\n"
            "token.set_transfer_burn_rate(0.0005) # 0.05% friction burn\n"
            "token.deploy()\n"
            "```\n\n"
            "Apakah ada parameter khusus yang ingin Anda tambahkan pada token ini?"
        )
    elif "least action" in message_lower or "mep" in message_lower or "hukum" in message_lower or "fisika" in message_lower:
        reply = (
            "Thermoledger menggunakan **Least Action Principle (Prinsip Aksi Terkecil)** pada konsensus L2.\n\n"
            "Bot L2 mengorganisasi transaksi di mempool agar transisi keadaan spin kisi L1 validator (ΔH) seminimal mungkin. "
            "Hal ini menurunkan hambatan termal sirkuit dan memotong gas fee hingga mencapai 0.00 Joule (bebas biaya)."
        )
    elif "faucet" in message_lower or "saldo" in message_lower or "minta" in message_lower:
        reply = (
            "Anda dapat meminta saldo testnet gratis sebesar 10 $DUIT melalui Panel Faucet di halaman `/scan` "
            "atau memanggil API `POST /api/v1/faucet` dengan mengirimkan payload JSON berisi alamat penerima."
        )
    elif "airdrop" in message_lower:
        reply = (
            "Airdrop searah dalam jumlah besar dapat memicu penumpukan panas termal di sirkuit.\n\n"
            "Gunakan fungsi `distribution_rate` pada modul `ThermoledgerAirdrop` untuk mengirimkan koin secara "
            "gradual (misal 10 wallet per blok L1) guna menjaga sirkuit tetap dingin di bawah batas 5.0 °C."
        )
    else:
        reply = (
            "Saya memahami Anda menanyakan tentang Thermoledger. Sebagai asisten pengembang, saya dapat membantu "
            "Anda merancang kontrak pintar TTS-20, mensimulasikan stress test termal jaringan, atau mengintegrasikan "
            "SDK Dart. Silakan periksa portal dokumentasi interaktif di halaman `/docs` untuk referensi API lengkap."
        )
        
    return {"reply": reply}

@app.get("/docs")
async def read_docs():
    return RedirectResponse(url="/docs.html")

@app.get("/scan")
async def read_scan():
    return RedirectResponse(url="/scan.html")

@app.get("/playground")
async def read_playground():
    return RedirectResponse(url="/playground.html")

# Intercept root page for custom subdomain routing
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    host = request.headers.get("host", "").lower()
    if "duitcard" in host:
        try:
            with open("static/duitcard.html", "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except Exception:
            pass
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index file not found: {e}")

# Mount frontend directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
