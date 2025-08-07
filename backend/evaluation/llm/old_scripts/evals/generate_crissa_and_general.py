# ruff: noqa


import asyncio

from backend.app.minutes.templates.crissa import generate_full_crissa
from backend.app.minutes.templates.general_style import generate_general_style_summary
from shared_utils.database.postgres_models import DialogueEntry

dialogue_entries = [
    DialogueEntry(
        speaker="Tania",
        text="Mr. Field, with regards to drug misuse, Mr. Field informed me that he started smoking weed when he was about 17 or 18 years old. It was all to do with the friendship group he was with. He smoked ketamine, he took ketamine, ecstasy and cocaine. now and then. And then from 21 to 22 years onwards, he moved into a house with other friends. Everyone there were drug users. Being around the drugs all the time made it feel more relaxed and made it feel like normal. His main use was cocaine. To begin with, he was sort of using bi-weekly, more so if there was a big event coming up. He wouldn't really just use it as a after work kind of thing. He doesn't talk to the co-defendant anymore and he doesn't actually speak to anybody from that house. He hasn't used any drugs since the offence happened and says that his partner is a very supportive is very supportive and is a very good protective factor in helping him stay off the drugs. She doesn't like drugs, so he hasn't used since. With regards to alcohol use, Mr. Field said that alcohol has never been a problem for him. He doesn't drink during the week. He might have a beer now and then at the weekend. He said that he, now he's older, he can't sort of cope with the alcohol the same as he used to. And he kind of, you know, would have more of a hangover. He has to get up for work at 4.30, 5am each day. So he doesn't, you know, he makes sure he doesn't drink and he knows when to stop. So alcohol is not an issue for him. It's not related to his offending. Emotional well-being, Mr. Field said that he's never had any issues or any problems in this area. His mother has Ms. and that, but she's always had it ever since he was born. So he's sort of just dealt with each stage and sort of lapse as they've come along. Never been on any antidepressants, no problems in that area. Thinking and behaviour, Mr. Field's offending would demonstrate sort of clear deficits in his thinking and sort of poor decision-making skills. He doesn't lose his temper that often. He's quite chilled out. He likes to use the gym, etc., etc. for his stress relief. Physical health, there are no issues, nothing that we need to be concerned about. He is well. In terms of attitudes, Mr. Field understands his sort of reasons behind his offending. He has no desire to use drugs again. He is motivated to continue with the path that he's on. He's in a very stable, supportive relationship. He's in full-time, secure employment. He just wants to get his order, his hours done and his order completed and get on with the rest of his life.",
        start_time=0.0,
        end_time=0.0,
    )
]


async def generate_crissa_and_general(dialogue_entries: list[DialogueEntry]):
    crissa_output = await generate_full_crissa(dialogue_entries, "test@test.com")
    general_output = await generate_general_style_summary(
        dialogue_entries, "test@test.com"
    )
    return crissa_output, general_output


if __name__ == "__main__":
    crissa_output, general_output = asyncio.run(
        generate_crissa_and_general(dialogue_entries)
    )

    print("CRISSA OUTPUT:")
    print(crissa_output)
    print("GENERAL OUTPUT:")
    print(general_output)
