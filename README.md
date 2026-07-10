# Gardening Project

## About this repo
I've even generated this readme with claude. This whole project is just me learning how to use claudecode and what is and isn't a good idea when using it. So far leared that using high confidense modles probbaly aren't worth the token cost.

This project is an exercise in **vibecoding** — building an application almost entirely through conversation with an AI coding assistant rather than hand-writing it. It's also my first time using Claude Code. I want to see how far I can get building the application below purely from the information I've given it, consulting me on the genuinely ambiguous decisions along the way rather than guessing.

See [CLAUDE.md](CLAUDE.md) for the locked technical decisions, data model, and the list of things Claude Code should stop and ask me about before implementing.

## Draft overview

This is my original draft description of the application, kept here as the source-of-truth intent behind the project.

I want to create an application that manages a garden for the end user.

The application should use a highly colourful pixilated retro art style that includes animated elements, such as trees and other plants swaying in the wind, and when relevant, clouds moving across a blue sky.

The application should be coded in python, and should follow the PEP 8 programming convension. The application should be written to be both simple and efficient as possible, with light to medium density of comments.

Upon loading, the application should have a menu which contains three options: create a new garden, open an exsisting garden and exit the application. The entire application should use the font DotGothic16, with headers written in semi bold 600 and text written in regular 400. The options should exsist in oval boxes that have a similar level of pixilation as the font.

I want claude to not halusinate, and consult with me when there are difficult logical steps to follow or unclear instructions with a set list of potential options to create the best soltion.

When creating a new garden, the application should give the user a chance to draw both the outline of the garden and the outline of flowerbeds in the garden. There should be a mechanism that indicates to the user critical dimentions of both the flower beds and overall garden to the end user (for example, if the beds are rectangular, the length and width of the beds should be indicated, similarly, if the bed is approximately a quater circle, the radius of curviture of the bed should be indicated to the end user). There should also be a function that indicates the total area of a bed to the end user. When creating the system that works out what "important" dimentions are, claude should consult with me.

There should be a way to add plants to the garden, with the user inputting important facts such as the expected diameter of the plant when it is fully grown, the expected high of the plant and the plant species. Claude should be integrated into the application and generate a set of four suggested sprite arts for the plant that the user can then select, which are then stored and used when the user "plants" the plant in the bed. The plants should also have attributes such as time since last watering, expected watering requirements (this will be calculated at a later date, once the application is working), and "health", which the user can select between four values for: doing too well, healthy, struggling, and dead. The plant's height should also be stored, alng with it's current diamter. When planting plants in the beds, the program should indicate when plants are too close to one another (their current diamters overlap), and when there might be a potential future problem (there projected diameters overlap by more than 30%).

The user should be able to update the plants in the garden's status, such as when they are watered, when they change condition and size. The user should also be able to plant plants in flower bed when they get planted.
