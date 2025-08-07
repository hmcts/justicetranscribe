# ruff: noqa

from backend.app.llm.llm_client import (
    LLMModel,
    structured_output_llm_completion_builder_func,
)
from litellm import BaseModel
from datetime import datetime


class OutputComparison(BaseModel):
    """Pydantic model for LLM-based output comparison."""

    confidence: int  # 1-10 scale
    reasoning: str
    key_differences: list[str]
    better_output: str  # "A", "B", or "draw"


class OutputQualityJudge:
    """LLM-based judge for comparing two outputs."""

    def __init__(self, judge_model: LLMModel = LLMModel.VERTEX_GEMINI_25_PRO):
        self.judge_model = judge_model
        self.comparison_completion = structured_output_llm_completion_builder_func(
            OutputComparison
        )

    async def compare_outputs(
        self, dialogue_entries: str, date_of_meeting: str, output_a: str, output_b: str
    ) -> OutputComparison:
        """
        Compare two outputs and determine which is better.

        Args:
            dialogue_entries: The original dialogue/transcript
            date_of_meeting: The date/datetime of the meeting
            output_a: First output (regular output)
            output_b: Second output (one-shot output)

        Returns:
            OutputComparison with judgment details
        """

        # Extract just the date part from the datetime string
        try:
            # Parse the ISO datetime string and extract just the date
            parsed_date = datetime.fromisoformat(date_of_meeting.replace("Z", "+00:00"))
            meeting_date = parsed_date.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            # Fallback: if parsing fails, try to extract date from the beginning of the string
            meeting_date = (
                date_of_meeting.split("T")[0]
                if "T" in date_of_meeting
                else date_of_meeting
            )

        # The original CRISSA prompt that was used to generate the outputs
        crissa_prompt = """You are an experienced senior probation officer in the UK. You are tasked with generating the full a CRISSA report based on a transcript of a supervision session with a Person on Probation. CRISSA is the framework used by probation officers in the UK to write case notes for supervision meetings with people on probation.

CRISSA SECTION GUIDELINES:
- Check in. Consider how the Person on Probation is presenting. What is their mood, attitude and demeanour?
- Review. Are there any new disclosures or changes in circumstances e.g., police contact, safeguarding, prohibited contact.
- Intervention. What intervention has taken place? If applicable, what worksheets were used? This section can be flexible - if the Person on Probation presents in crisis, then the crisis area can be addressed as a priority instead of an intervention. Identify any purposeful work the Probation Practitioner initiated, even if the word intervention is never spoken. Look for cues like "today we'll talk about...", "let's work through this worksheet...". In the intervention section, it's important to include details of the conversation that focuses on thinking, emotions, and behaviour, and how they interact. The intervention section is the most important and detailed section of CRISSA.
- Summary. How did the Person on Probation engage in the meeting? Any new risk factors identified? Did the Person on Probation make any significant discolsures?
- Set Task. What tasks have been agreed for the Probation Practitioner and the Person on Probation to complete and by when?
- Appointment. When is the next appointment and with whom? How will this take place e.g., in person or remotely. Do not hallucinate an appointment date if an appointment date was not discussed.

WRITING GUIDELINES:
- Write concisely and clearly.
- Include relevant context or quotations where it aids understanding.
- Do not ever duplicate content or write repetitively.
- Make sure you think carefully and clearly about pulling out the right details for writing a very high quality CRISSA report.
- Do not hallucinate any information that is not in the transcript provided. Particularly if the transcript does not seem to correspond to a probation meeting, please do not hallucinate details from the examples or elsewhere.
- Always include the headers for the section.
- Do not include any preamble like 'Here is your CRISSA:'
- Keep in mind that although the CRISSA examples below are relatively long, you can output shorter content if the transcript is short or less detailed. Don't be afraid to return a concise CRISSA. 

EXAMPLES:

EXAMPLE 1:
**Check in** – X initially stated his week had been “alright” with no incidents to report. 
**Review** - X reports that he is doing well and has no new concerns to raise. X states there hasn't been any update from his MOSAVO officer regarding his query regarding selling electronics, however he appeared less motivated today to chase this up with her and feels as though the situation has been finished now and police are not overly concerned. 
**Intervention** - During today’s session, X revisited last week’s exploration of the internet’s positives and negatives and said he had a meaningful family discussion that unearthed further examples. This take-home reflection shows he is applying office work in his personal life and involving relatives in the process. Its encouraging that he is involving his family. He said looking back he cannot fathom how he went down the “rabbit hole” into his offending and used last week’s list to explore this. We completed M4C (Smarter Internet Use) Exercise 2. 

Using the family’s expanded list, we traced how everyday online behaviour can escalate. Starting with ordering groceries to meet the basic need to eat, we discussed how internet use can foster healthier habits, recipe sites, workout videos or slide into harmful content such as pro-eating-disorder forums. X noted this resonated with his past struggle with bulimia. 

We then focused on sexual use of the internet. X acknowledged a daily habit of masturbating (often with his partner) mainly for stress relief. He views consensual sex positively and clearly understands that lack of consent constitutes an offence. Together we mapped how pornography can progress from mainstream content to riskier venues, chat rooms, torrent sites and the deep web, fuelled by desensitisation. X recognised this trajectory in his own offending: a high sex drive established in adolescence, heavy pornography consumption and a gradual pursuit of more “extreme” material. 

X engaged openly and demonstrated growing insight into how acceptable online behaviours can drift into harmful ones when left unchecked. Future sessions will build on this awareness, particularly around why children cannot give consent and how to establish healthier internet boundaries. 

**Summary** - X engaged openly and demonstrated good insight into triggers and balanced internet use. No new risk factors, but online content remains a dynamic area to monitor. Licence conditions and safeguarding around under-age material reinforced. He reports that his accommodation status remains the same, and he continues in his relationship with Darren without concern. He states that he still feels as though he is managing his mental health effectively, and continues to abstain from any offending behaviours 
**Set actions** - X to bring a reflection worksheet listing three everyday online activities with one benefit and one risk for each by next appointment. PP to email balanced-use articles and breathing-video link to X by Sunday and remain contact point for any MOSAVO developments.  
**Appointment** - Verbally agreed for 15/11/24 at 14:00. 

EXAMPLE 2:
**Check in** - X attended on time. He seemed low in mood and appeared unkempt. He disclosed he relapsed on heroin a few days ago. He stated that he felt disappointed as he had been clean for 6 months. I noted that he did not appear under the influence of substances during our supervision.
**Review** - X reported that he had not attended his drug appointments. He was encouraged him attend with his drugs worker to gain support with managing substance misuse relapse. I offered to facilitate this meeting by making the next appointment a joint 4-way with the keyworker and his IOM police officer to which he agreed. As X's has a history of acquisitive offending to fund his substance misuse, I explored how he funded his drug misuse. He disclosed using his benefits and expressed being "unsure" what he would do if he ran out of money. He maintained that he has had no contact with the police or reoffended to fund drug habit. Mr X's risk of reoffending is assessed to be increasing as there has been a change in circumstance. X has relapsed on substance misuse. His offending history indicates that he has the propensity to resort to burglary/theft offending behaviours to fund his drug habit. The risk of serious harm is assessed to remain at medium.
**Intervention** - The plan for the session was to complete steppingstones intervention. However, due to X presenting in crisis, the session focused on monitoring/control and treatment to manage risk factors presented. A non-structured intervention was completed with the aim of addressing dynamic risk factors and encourage supporting desistance through motivational interviewing for X to engage with substance misuse services and IOM police.
**Summary** - X appeared somewhat engaged with the session but his disclosure regarding substance misuse issue is a concern. His relapse heightens the risk of reoffending which require action (see set tasks) to mitigate the risks.
**Set task** - PP will complete the following: - Liaise with IOM officer and keyworker and arrange a 4-way meeting for X's next appointment. - Complete BIU check with the IOM team to see if X has come to their notice. - Liaise with X's keyworker before next appointment
**Appointment** - Next appointment given verbally for 01/07/2023 at 10am at the office.

Please generate a full high-quality CRISSA report."""

        judge_prompt = """You are an expert evaluator of UK probation case notes, specifically CRISSA reports. You need to compare two different CRISSA outputs for the same supervision session transcript and determine which one is better.

CONTEXT - THE ORIGINAL TASK:
The LLM that generated these outputs was given the following instructions:

{crissa_prompt}

EVALUATION CRITERIA:
Based on the original CRISSA guidelines, evaluate both outputs on:

1. **CRISSA Structure Adherence**: 
   - Does it follow the proper CRISSA sections (Check in, Review, Intervention, Summary, Set Task, Appointment)?
   - Are the section headers included?
   - Is each section appropriate to its purpose?

2. **Content Quality per Section**:
   - Check in: Captures mood, attitude, demeanour
   - Review: Identifies new disclosures/changes in circumstances  
   - Intervention: Details purposeful work, thinking/emotions/behaviour interactions (most important section)
   - Summary: Engagement level, new risk factors, significant disclosures
   - Set Task: Clear, actionable tasks with timelines
   - Appointment: Next appointment details (no hallucination if not discussed)

3. **Writing Guidelines Compliance**:
   - Concise and clear writing
   - Relevant context/quotations included
   - No content duplication or repetition
   - No hallucinated information
   - Appropriate level of detail for transcript length

4. **Professional Standards**:
   - Appropriate probation terminology
   - Risk assessment considerations
   - Safeguarding awareness
   - Person-centered language

5. **Accuracy to Transcript**: 
   - All content grounded in the actual transcript
   - No fabricated details or assumptions
   - Proper interpretation of dialogue

Original Transcript:
{dialogue_entries}

Output A:
{output_a}

Output B: 
{output_b}

The date this meeting took place is: {date_of_meeting}

Note that the LLM generating CRISSA is provided the date the meeting took place which it uses for the appointment section. So don't assume it is hallucinating an appointment date if one is not discussed in the transcript.

Please analyze both outputs carefully against the CRISSA framework and determine which one better fulfills the original task requirements.

Your response should indicate:
- Which output is better: "A", "B", or "draw" (if both outputs are very similar in quality)
- Your confidence level (1-10, where 10 is extremely confident)
- Detailed reasoning focusing on how well each output meets the CRISSA requirements
- Key differences you observed between the outputs, particularly regarding CRISSA structure and content quality

Use "draw" when:
- Both outputs are of very similar overall quality
- Any differences between outputs are minor and don't significantly impact the CRISSA quality
- Both outputs meet the CRISSA requirements adequately with no clear winner

Think step by step through each CRISSA section and writing guideline before making your final judgment."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert evaluator of UK probation documentation with deep knowledge of the CRISSA framework and years of experience in criminal justice case management.",
            },
            {
                "role": "user",
                "content": judge_prompt.format(
                    crissa_prompt=crissa_prompt,
                    dialogue_entries=dialogue_entries,
                    date_of_meeting=meeting_date,
                    output_a=output_a,
                    output_b=output_b,
                ),
            },
        ]

        try:
            result = await self.comparison_completion(
                model=self.judge_model,
                messages=messages,
                temperature=0,  # Low temperature for consistent evaluation
            )
            # check if result is a draw and print that it is a draw
            if result.better_output == "draw":
                print("Draw")
            return result
        except Exception as e:
            print(f"Error in output comparison: {e}")
            # Return a default comparison in case of error
            return OutputComparison(
                better_output="A",  # Default to first output
                confidence=1,
                reasoning=f"Error occurred during comparison: {e}",
                key_differences=[],
            )
