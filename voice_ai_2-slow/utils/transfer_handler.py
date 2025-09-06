# utils/transfer_handler.py - FIXED VERSION
"""
Call transfer utility for Voice AI system - FIXED
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from enum import Enum

from livekit import api
from livekit.protocol import sip as proto_sip

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

from logging_config import create_call_logger

transfer_logger = create_call_logger("transfer")

class CallTransferHandler:
    def __init__(self):
        self.livekit_api = None
        
    async def initialize(self):
        try:
            self.livekit_api = api.LiveKitAPI(
                url=config.livekit_url,
                api_key=config.livekit_api_key,
                api_secret=config.livekit_api_secret
            )
            transfer_logger.info("✅ Transfer handler initialized")
            return True
        except Exception as e:
            transfer_logger.error(f"❌ Transfer handler init failed: {e}")
            return False
    
    async def transfer_to_human(self, room_name: str, participant_identity: str) -> Dict[str, Any]:
        """Transfer call to human agent using extension 2020"""
        try:
            if not self.livekit_api:
                await self.initialize()
            
            # Use extension 2020 as requested
            transfer_to = f"sip:2020@15.204.54.41"
            
            transfer_request = proto_sip.TransferSIPParticipantRequest(
                room_name=room_name,
                participant_identity=participant_identity,
                transfer_to=transfer_to,
                play_dialtone=False
            )
            
            await self.livekit_api.sip.transfer_sip_participant(transfer_request)
            
            transfer_logger.info(f"Transfer successful to {transfer_to}")
            
            return {
                "result": "success",
                "transfer_to": transfer_to,
                "message": "Transfer completed successfully"
            }
            
        except Exception as e:
            transfer_logger.error(f"Transfer failed: {e}")
            return {
                "result": "failed",
                "message": str(e)
            }
    def detect_transfer_request(self, user_message: str) -> bool:
        transfer_keywords = [
            "human", "agent", "person", "transfer", "speak with", 
            "talk to", "customer service", "representative"
        ]
        user_lower = user_message.lower()
        return any(keyword in user_lower for keyword in transfer_keywords)

call_transfer_handler = CallTransferHandler()