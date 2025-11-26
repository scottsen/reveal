package com.example.demo;

import java.util.List;
import java.util.ArrayList;
import java.io.IOException;

/**
 * Simple Hello World application demonstrating Java features.
 */
public class HelloWorld {

    private static final String GREETING = "Hello";
    private String name;

    /**
     * Constructor for HelloWorld.
     * @param name The name to greet
     */
    public HelloWorld(String name) {
        this.name = name;
    }

    /**
     * Get the greeting message.
     * @return The formatted greeting
     */
    public String getGreeting() {
        return String.format("%s, %s!", GREETING, name);
    }

    /**
     * Print the greeting to console.
     */
    public void printGreeting() {
        System.out.println(getGreeting());
    }

    /**
     * Static utility method to create greetings for multiple names.
     * @param names List of names to greet
     * @return List of greetings
     */
    public static List<String> greetMultiple(List<String> names) {
        List<String> greetings = new ArrayList<>();
        for (String name : names) {
            HelloWorld hw = new HelloWorld(name);
            greetings.add(hw.getGreeting());
        }
        return greetings;
    }

    /**
     * Main entry point.
     * @param args Command line arguments
     * @throws IOException if something goes wrong
     */
    public static void main(String[] args) throws IOException {
        if (args.length == 0) {
            System.out.println("Usage: HelloWorld <name>");
            System.exit(1);
        }

        HelloWorld hello = new HelloWorld(args[0]);
        hello.printGreeting();

        // Demonstrate greetMultiple
        List<String> names = List.of("Alice", "Bob", "Charlie");
        List<String> greetings = greetMultiple(names);
        greetings.forEach(System.out::println);
    }
}

/**
 * Interface for greeting strategies.
 */
interface GreetingStrategy {
    String greet(String name);
}

/**
 * Enum for greeting types.
 */
enum GreetingType {
    FORMAL("Good day"),
    CASUAL("Hey"),
    FRIENDLY("Hello");

    private final String prefix;

    GreetingType(String prefix) {
        this.prefix = prefix;
    }

    public String getPrefix() {
        return prefix;
    }
}
