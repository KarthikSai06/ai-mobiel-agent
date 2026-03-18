import logging
import time
import os
from device.adb_controller import AdbController
from ui.dump_ui import dump_ui_hierarchy
from ui.ui_parser import parse_ui_xml, format_ui_elements_for_llm
from executor.skill_executor import SkillExecutor
from planner.llm_planner import LLMPlanner

logger = logging.getLogger(__name__)

class AgentLoop:
    def __init__(self, device_id: str = None):
        from config import settings
        self.adb = AdbController(adb_path=settings.ADB_PATH)
        self.device_id = device_id
        
                                                            
        if not self.device_id:
             devices = self.adb.get_devices()
             if devices:
                 self.device_id = devices[0]
                 logger.info(f"Using device: {self.device_id}")
             else:
                 logger.error("No Android devices found. Ensure ADB is connected and authorized.")

        self.executor = SkillExecutor(self.adb, self.device_id)
        self.planner = LLMPlanner()
        self.history = []           # list of {"action": str, "outcome": str}
        self.last_ui_str = ""
        self.stuck_counter = 0

    def run(self, task: str, max_steps: int = 15):
        """
        Orchestrates the main execution loop: Dump -> Parse -> Plan -> Execute
        """
        logger.info(f"Starting agent task: {task}")
        
        for step in range(max_steps):
            logger.info(f"=== Step {step+1}/{max_steps} ===")
            
                        
            xml_path = dump_ui_hierarchy(self.adb, self.device_id)
            if not xml_path:
                logger.warning("UI dump failed — screen may have a fullscreen video/ad. Trying vision recovery...")
                from config import settings
                screenshot_path = os.path.join(settings.SCREENSHOTS_DIR, f"recovery_{step}.png")
                if self.adb.take_screenshot(screenshot_path, self.device_id):
                    recovery = self.planner.get_action_from_screenshot(task, screenshot_path)
                    logger.info(f"Vision recovery action: {recovery}")
                    if recovery.get("skill") == "tap":
                        self.executor.execute_skill("tap", recovery["args"])
                        time.sleep(2.5)  # wait for screen to settle after tap

                        # Check if the task is now complete (e.g. video is playing)
                        verify_path = os.path.join(settings.SCREENSHOTS_DIR, f"verify_{step}.png")
                        if self.adb.take_screenshot(verify_path, self.device_id):
                            if self.planner.check_task_done_from_screenshot(task, verify_path):
                                logger.info("Task confirmed complete via screenshot. Done!")
                                break  # clean exit — task succeeded
                        continue  # not done yet, retry this step
                logger.error("Vision recovery also failed. Aborting.")
                break
                
                                  
            ui_elements = parse_ui_xml(xml_path)
            ui_str = format_ui_elements_for_llm(ui_elements)
            logger.info(f"UI Elements sent to LLM:\n{ui_str}")
            
                                                                          
            is_stuck = False
            if self.last_ui_str == ui_str:
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
                
            self.last_ui_str = ui_str

            
            if self.stuck_counter >= 1:                                               
                from config import settings
                if getattr(settings, "ENABLE_VISION_FALLBACK", False):
                    logger.warning("Agent appears stuck. Triggering Moondream Vision Fallback...")
                    screenshot_path = os.path.join(settings.SCREENSHOTS_DIR, f"stuck_{step}.png")
                    if self.adb.take_screenshot(screenshot_path, self.device_id):
                        vision_insight = self.planner.analyze_with_vision(task, screenshot_path)
                        self.stuck_counter = 0                                     
                    else:
                        logger.error("Failed to capture screenshot for vision fallback.")
                        vision_insight = None
                else:
                    vision_insight = None
            else:
                vision_insight = None
                        
            action_plan = self.planner.plan_next_action(task, ui_str, self.history, vision_insight)
                
            skill_name = action_plan.get("skill")
            args = action_plan.get("args", {})
            
            logger.info(f"Planned Action -> SKILL: {skill_name}, ARGS: {args}")
            
                                                                    
            self.executor.set_last_elements(ui_elements)

                               
            if skill_name == "done":
                logger.info("Task marked as DONE by planner.")
                break
                
            # Capture UI *before* the action (already in ui_str) and execute
            success = self.executor.execute_skill(skill_name, args)

            # --- Fix 2: outcome tracking ---
            # Re-dump UI after the action to detect whether anything changed
            post_xml_path = dump_ui_hierarchy(self.adb, self.device_id)
            post_ui_str = ""
            if post_xml_path:
                post_elements = parse_ui_xml(post_xml_path)
                post_ui_str = format_ui_elements_for_llm(post_elements)

            if not success:
                outcome = "FAILED"
                logger.warning("Action execution failed or returned False.")
            elif post_ui_str and post_ui_str == ui_str:
                outcome = "NO_CHANGE"
                logger.info("Action executed but UI did not change.")
            else:
                outcome = "SUCCESS"

            action_record = f"{skill_name}({args})"
            self.history.append({"action": action_record, "outcome": outcome})
            logger.info(f"History entry: {action_record} → {outcome}")

            # --- Fix 3: loop detector ---
            # If the last 3 actions are identical, trigger a recovery press BACK
            if (len(self.history) >= 3 and
                    self.history[-1]["action"] == self.history[-2]["action"] == self.history[-3]["action"]):
                logger.warning(
                    f"Loop detected: '{action_record}' repeated 3 times. Pressing BACK to recover."
                )
                self.executor.execute_skill("press_key", {"key": "BACK"})
                time.sleep(1.5)
            
                                                            
            time.sleep(2.0)
            
        else:
            logger.warning(f"Task reached maximum steps ({max_steps}) without finishing.")
            
        logger.info("Agent loop finished.")
