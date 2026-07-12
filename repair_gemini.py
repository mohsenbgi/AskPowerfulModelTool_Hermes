def _keep_last_repeated_block(text: str) -> str:
    """
    Repairs text that has been repeated due to a streaming bug.
    A streaming bug occurs when a generator repeatedly yields the accumulated 
    text instead of just the new delta. This causes the string to look like:
    S = A_1 + A_2 + ... + A_n, where each A_i is a prefix of A_{i+1}.
    This function finds the longest valid final chunk A_n and safely removes the buggy prefixes.
    """
    if not text:
        return text
        
    n = len(text)
    
    # We iterate k backwards. k is the candidate start index for the final correct text (A_n).
    # Finding the largest valid k guarantees we return the shortest fully-repaired string,
    # ensuring we don't accidentally leave partial repetitions behind.
    for k in range(n - 1, 0, -1):
        target_str = text[k:]
        
        # Heuristic 1: A legitimate target text must be substantial. 
        if len(target_str) < 10:
            continue
            
        prefix_str = text[:k]
        
        # Heuristic 2: The repaired target MUST start with the same character as the full string.
        # This acts as an extreme fast-path filter.
        if target_str[0] != prefix_str[0]:
            continue
            
        # Heuristic 3: A valid final text block must have words/spacing.
        # This prevents squashing intentional repeating characters like "aaaaa..."
        if " " not in target_str and "\n" not in target_str:
            continue
            
        memo = {}
        
        # Backtracking search to verify if prefix_str is composed of valid growing prefixes of target_str
        def dfs(index: int, last_length: int, chunk_count: int) -> bool:
            # Base case: we successfully partitioned the prefix string
            if index == len(prefix_str):
                if chunk_count >= 2:
                    return len(target_str) >= last_length
                elif chunk_count == 1:
                    # Allow 2-chunk streaming bugs (A_1 + A_2) only if the final text 
                    # is significantly longer than the buggy prefix
                    return len(target_str) >= last_length + 5
                return False
                
            cc_state = min(chunk_count, 2)
            if (index, last_length, cc_state) in memo:
                return memo[(index, last_length, cc_state)]
                
            # Find the maximum matching prefix length between the remaining prefix string and the target
            limit = min(len(prefix_str) - index, len(target_str))
            max_match = 0
            while max_match < limit and prefix_str[index + max_match] == target_str[max_match]:
                max_match += 1
                
            # Try all valid lengths greedily
            for l in range(max_match, 0, -1):
                # The lengths of the streaming chunks must STRICTLY grow (A_1 < A_2 < ...)
                # EXCEPT if the stream stalled at the end, in which case the chunks exactly equal the final target.
                if l <= last_length and l != len(target_str):
                    continue
                    
                # The very first chunk must be strictly smaller than the final output
                # to guarantee it's a growing stream and not a fully repeating sequence
                if chunk_count == 0 and l == len(target_str):
                    continue
                    
                if dfs(index + l, l, chunk_count + 1):
                    memo[(index, last_length, cc_state)] = True
                    return True
                    
            memo[(index, last_length, cc_state)] = False
            return False
        
        # If the prefix can be decomposed into prefixes of target_str, we found our bug fix!
        if dfs(0, 0, 0):
            return target_str
            
    return text

sample_1 = "Hey thereHey there! How's it going? What's on your mind today?Hey there! How's it going? What's on your mind today?"

sample_2 = """To addTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) projectTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.ktsTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

###To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.ktsTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependenciesTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implementTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project withTo add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project with Gradle files, and you're ready to run it on Android, iOS, or any other supported KMP targets.To add Realm (MongoDB Realm / Atlas Device Sync Kotlin SDK) to a Kotlin Multiplatform (KMP) project, follow these steps:

### 1. Add the Plugin and Dependency
Open your root `build.gradle.kts` file and add the Realm plugin. 

```kotlin
plugins {
    // Check for the latest version of Realm Kotlin
    id("io.realm.kotlin") version "3.0.0" apply false 
}
```

### 2. Apply the Plugin and Add Dependencies in your Shared Module
Open your shared module's `build.gradle.kts` (usually `:shared` or `:common`). Apply the plugin at the top and add the library to your `commonMain` dependencies.

```kotlin
plugins {
    id("io.realm.kotlin")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            // Core Realm database functionality
            implementation("io.realm.kotlin:library-base:3.0.0")
            
            // Optional: If you need Atlas Device Sync features
            // implementation("io.realm.kotlin:library-sync:3.0.0") 
        }
    }
}
```

### 3. Define Your Data Models
Create your database models in `commonMain`. They must implement `RealmObject` and have an empty constructor (or default values for all properties).

```kotlin
import io.realm.kotlin.types.RealmObject
import io.realm.kotlin.types.annotations.PrimaryKey
import org.mongodb.kbson.ObjectId

class Dog : RealmObject {
    @PrimaryKey 
    var _id: ObjectId = ObjectId()
    var name: String = ""
    var age: Int = 0
}
```

### 4. Initialize and Use Realm
You can now open a Realm instance and use it directly in your common code.

```kotlin
import io.realm.kotlin.Realm
import io.realm.kotlin.RealmConfiguration
import io.realm.kotlin.ext.query

class DatabaseService {
    private val config = RealmConfiguration.Builder(schema = setOf(Dog::class))
        .name("myrealm.realm")
        .build()
        
    private val realm = Realm.open(config)

    // Write data
    suspend fun addDog(dogName: String, dogAge: Int) {
        realm.write {
            copyToRealm(Dog().apply {
                name = dogName
                age = dogAge
            })
        }
    }

    // Read data
    fun getAllDogs(): List<Dog> {
        return realm.query<Dog>().find()
    }
}
```

Sync your project with Gradle files, and you're ready to run it on Android, iOS, or any other supported KMP targets."""

sample_3 = """The capitalThe capital of France is **Paris**. 

It is located in the north-central part of the countryThe capital of France is **Paris**. 

It is located in the north-central part of the country, along the Seine River.The capital of France is **Paris**. 

It is located in the north-central part of the country, along the Seine River."""

sample_4 = """Here isHere is the quickest way to create and run a "Hello, World!" application in .NET usingHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new consoleHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
NavigateHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.csHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the applicationHere is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
```text
Hello, World!
```Here is the quickest way to create and run a "Hello, World!" application in .NET using the command line.

### 1. Create the Project
Open your terminal or command prompt and run the following command to create a new console application:

```bash
dotnet new console -o HelloWorld
```

### 2. View the Code
Navigate into the newly created directory:
```bash
cd HelloWorld
```

If you open the `Program.cs` file, you will see .NET's modern, streamlined top-level statement:

```csharp
// Program.cs
Console.WriteLine("Hello, World!");
```

### 3. Run the Application
Execute the application with this command:

```bash
dotnet run
```

**Output:**
```text
Hello, World!
```"""

sample_5 = """Right?Right? I like to think so. 

What's on your mind? How can I help you outRight? I like to think so. 

What's on your mind? How can I help you out today?Right? I like to think so. 

What's on your mind? How can I help you out today?"""

print("sample 1: \n")
print(_keep_last_repeated_block(sample_1))

print("\n \n")
print("sample 2: \n")
print(_keep_last_repeated_block(sample_2))

print("\n \n")
print("sample 3: \n")
print(_keep_last_repeated_block(sample_3))

print("\n \n")
print("sample 4: \n")
print(_keep_last_repeated_block(sample_4))

print("\n \n")
print("sample 5: \n")
print(_keep_last_repeated_block(sample_5))