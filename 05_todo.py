tasks = []

while True:
    print("\n====================================")
    print("        TO-DO LIST – TASK MANAGER")
    print("====================================")
    print("1. Add a New Task")
    print("2. View All Tasks")
    print("3. Delete a Task")
    print("4. Exit the Program")
    print("====================================")

    choice = input("Please select an option (1–4): ").strip()

    if not choice.isdigit():
        print("Invalid input. Please enter numbers only.")
        continue

    choice = int(choice)

    if choice == 1:
        print("\n--- Add Tasks (type 'done' when you finish adding tasks) ---")
        count = 0

        while True:
            new_task = input("Enter a task: ").strip()

            if new_task.lower() == "done":
                if count > 0:
                    print(f"{count} task(s) have been successfully added to your To-Do List.")
                else:
                    print("No tasks were added.")
                break
            
            # Prevent adding completely blank tasks
            if not new_task:
                print("Task cannot be empty. Please try again.")
                continue

            tasks.append(new_task)
            count += 1

    elif choice == 2:
        if not tasks:
            print("\nYour task list is currently empty.")
        else:
            print("\n--- Your Current Tasks ---")
            for i, task in enumerate(tasks, 1):
                print(f"{i}. {task}")

    elif choice == 3:
        if not tasks:
            print("\nThere are no tasks available to delete.")
        else:
            print("\n--- Select a Task to Delete ---")
            for i, task in enumerate(tasks, 1):
                print(f"{i}. {task}")

            num = input("Enter the number of the task you want to delete: ").strip()

            if not num.isdigit():
                print("Invalid input. Please enter a valid task number.")
                continue

            num = int(num)

            if 1 <= num <= len(tasks):
                print("\nSelected Task:")
                print(f">> {tasks[num - 1]}")

                confirm = input("Are you sure you want to delete this task? (yes/no): ").strip().lower()

                if confirm == "yes":
                    deleted_task = tasks.pop(num - 1)
                    print("\n*** TASK DELETED SUCCESSFULLY ***")
                    print(f"Deleted Task: {deleted_task}")

                    if not tasks:
                        print("Your task list is now empty.")
                    else:
                        print("\n--- Updated Task List ---")
                        for i, task in enumerate(tasks, 1):
                            print(f"{i}. {task}")
                else:
                    print("Deletion cancelled. The task was not deleted.")
            else:
                print("Invalid task number.")

    elif choice == 4:
        print("\nThank you for using the To-Do List.")
        print("The program has been closed.")
        break

    else:
        print("Please select a valid option between 1 and 4.")